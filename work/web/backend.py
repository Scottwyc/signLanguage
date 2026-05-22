#!/usr/bin/env python3
"""Web API for the signLanguage Holistic scoring MVP.

The service serves a browser frontend and keeps one MediaPipe Holistic worker
alive in a subprocess. Browser frames are sent as JPEG base64 slices, converted
to raw Holistic JSON by the worker, then scored against the cached demo
templates with the existing scoring MVP module.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


REPO_ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = REPO_ROOT / "work"
SCRIPT_DIR = WORK_DIR / "scripts"
STATIC_DIR = Path(__file__).resolve().parent / "static"
WORKER_SCRIPT = SCRIPT_DIR / "holistic_worker_daemon.py"
TEMPLATE_ROOT = WORK_DIR / "generated/scoring_mvp_run2/all_demo_step4_worker_cache_v2/results"
OUTPUT_ROOT = WORK_DIR / "generated/web_scoring_mvp"
LOG_DIR = WORK_DIR / "logs"
DEMO_VIDEO_ROOT = REPO_ROOT / "data/Demo词汇视频/Demo词汇视频"
SEMANTIC_PROFILE_JSON = WORK_DIR / "generated/scoring_semantic_profiles/sign_semantic_weights.json"
DEFAULT_MODEL_COMPLEXITY = 1

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from score_holistic_sequence_mvp import load_sequence, run_pair  # noqa: E402


class ScoreRequest(BaseModel):
    target_word: str = Field(default="花", description="Template word/folder name")
    fps: float = Field(default=5.0, gt=0.0, le=60.0)
    duration_sec: Optional[float] = Field(default=None, ge=0.0, le=30.0)
    frame_indices: Optional[List[int]] = None
    frames: List[Dict[str, Any]] = Field(default_factory=list)
    wait_for_ready_sec: float = Field(default=600.0, ge=0.0, le=900.0)


class HolisticWorkerService:
    def __init__(self, worker_script: Path, model_complexity: int = DEFAULT_MODEL_COMPLEXITY) -> None:
        self.worker_script = worker_script
        self.model_complexity = model_complexity
        self.process: Optional[subprocess.Popen[str]] = None
        self.status = "stopped"
        self.error: Optional[str] = None
        self.ready_payload: Optional[Dict[str, Any]] = None
        self.started_at: Optional[str] = None
        self.ready_at: Optional[str] = None
        self.stderr_log: Optional[Path] = None
        self._ready_event = threading.Event()
        self._request_lock = threading.Lock()
        self._lifecycle_lock = threading.Lock()
        self._stderr_handle = None

    def start_async(self) -> None:
        with self._lifecycle_lock:
            if self.status in {"starting", "ready"}:
                return
            self.status = "starting"
            self.error = None
            self.ready_payload = None
            self.ready_at = None
            self.started_at = datetime.now().isoformat(timespec="seconds")
            self._ready_event.clear()
            thread = threading.Thread(target=self._start_worker, name="holistic-worker-start", daemon=True)
            thread.start()

    def _start_worker(self) -> None:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_name = f"web_holistic_worker_{datetime.now().strftime('%Y%m%d_%H%M%S')}.stderr.log"
        self.stderr_log = LOG_DIR / log_name
        try:
            self._stderr_handle = self.stderr_log.open("a", encoding="utf-8")
            cmd = [
                sys.executable,
                str(self.worker_script),
                "--model-complexity",
                str(self.model_complexity),
            ]
            self.process = subprocess.Popen(
                cmd,
                cwd=str(SCRIPT_DIR),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=self._stderr_handle,
                text=True,
                bufsize=1,
            )
            if self.process.stdout is None or self.process.stdin is None:
                raise RuntimeError("worker pipes are not available")
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError("worker exited before ready message")
            payload = json.loads(line)
            if payload.get("type") != "ready":
                raise RuntimeError(f"unexpected worker startup payload: {payload}")
            self.ready_payload = payload
            self.ready_at = datetime.now().isoformat(timespec="seconds")
            self.status = "ready"
            self._ready_event.set()
        except Exception as exc:
            self.error = str(exc)
            self.status = "error"
            self._ready_event.set()

    def wait_ready(self, timeout_sec: float) -> None:
        self.start_async()
        if not self._ready_event.wait(timeout=max(0.0, timeout_sec)):
            raise TimeoutError("Holistic worker is still starting")
        if self.status != "ready":
            raise RuntimeError(self.error or f"Holistic worker status is {self.status}")

    def request(self, payload: Dict[str, Any], timeout_sec: float = 600.0) -> Dict[str, Any]:
        self.wait_ready(timeout_sec)
        with self._request_lock:
            if self.process is None or self.process.stdin is None or self.process.stdout is None:
                raise RuntimeError("worker process is not available")
            if self.process.poll() is not None:
                self.status = "error"
                self.error = f"worker process exited with code {self.process.returncode}"
                self._ready_event.set()
                raise RuntimeError(self.error)
            self.process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
            self.process.stdin.flush()
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError("worker returned empty response")
            response = json.loads(line)
            if response.get("type") == "error":
                raise RuntimeError(str(response.get("error") or response))
            return response

    def snapshot(self) -> Dict[str, Any]:
        proc_state = None
        if self.process is not None:
            proc_state = {
                "pid": self.process.pid,
                "returncode": self.process.poll(),
            }
        return {
            "status": self.status,
            "started_at": self.started_at,
            "ready_at": self.ready_at,
            "ready_payload": self.ready_payload,
            "error": self.error,
            "stderr_log": str(self.stderr_log) if self.stderr_log else None,
            "process": proc_state,
        }

    def shutdown(self) -> None:
        with self._lifecycle_lock:
            proc = self.process
            if proc is not None and proc.poll() is None and proc.stdin is not None:
                try:
                    proc.stdin.write(json.dumps({"cmd": "shutdown"}, ensure_ascii=False) + "\n")
                    proc.stdin.flush()
                    proc.wait(timeout=20)
                except Exception:
                    proc.terminate()
            self.status = "stopped"
            self._ready_event.clear()
            if self._stderr_handle is not None:
                try:
                    self._stderr_handle.close()
                except Exception:
                    pass


worker_service = HolisticWorkerService(WORKER_SCRIPT)
app = FastAPI(title="signLanguage Scoring MVP", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _template_path(word: str) -> Path:
    direct = TEMPLATE_ROOT / word / f"{word}_holistic_results.json"
    if direct.exists():
        return direct
    folder = TEMPLATE_ROOT / word
    matches = sorted(folder.glob("*_holistic_results.json")) if folder.exists() else []
    if matches:
        return matches[0]
    raise KeyError(word)


def _reference_video_path(word: str) -> Path:
    direct = DEMO_VIDEO_ROOT / f"{word}.mp4"
    if direct.exists():
        return direct
    matches = sorted(DEMO_VIDEO_ROOT.glob(f"{word}.*"))
    for item in matches:
        if item.suffix.lower() == ".mp4":
            return item
    raise KeyError(word)


def _semantic_profile_item(word: str) -> Optional[Dict[str, Any]]:
    if not SEMANTIC_PROFILE_JSON.exists():
        return None
    try:
        payload = json.loads(SEMANTIC_PROFILE_JSON.read_text(encoding="utf-8"))
        profile = (payload.get("profiles") or {}).get(word)
        if profile is None and "（" in word:
            profile = (payload.get("profiles") or {}).get(word.split("（", 1)[0])
        if profile is None:
            return None
        return {
            "profile_version": payload.get("version"),
            "description": profile.get("description"),
            "group_weights": profile.get("group_weights"),
            "focus_groups": profile.get("focus_groups"),
            "allow_hand_swap": profile.get("allow_hand_swap"),
        }
    except Exception:
        return None


def _list_templates() -> List[Dict[str, Any]]:
    templates: List[Dict[str, Any]] = []
    if not TEMPLATE_ROOT.exists():
        return templates
    for folder in sorted([item for item in TEMPLATE_ROOT.iterdir() if item.is_dir()], key=lambda p: p.name):
        matches = sorted(folder.glob("*_holistic_results.json"))
        if not matches:
            continue
        count = None
        fps = None
        try:
            payload = json.loads(matches[0].read_text(encoding="utf-8"))
            count = len(payload.get("records") or [])
            fps = payload.get("fps")
        except Exception:
            pass
        item = {
            "word": folder.name,
            "label": folder.name,
            "template_json": str(matches[0]),
            "records": count,
            "fps": fps,
        }
        try:
            ref = _reference_video_path(folder.name)
            item["reference_video"] = str(ref)
            item["reference_video_url"] = f"/api/reference-video/{folder.name}"
        except KeyError:
            item["reference_video"] = None
            item["reference_video_url"] = None
        item["semantic_profile"] = _semantic_profile_item(folder.name)
        templates.append(item)
    return templates


@app.on_event("startup")
def _startup() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    worker_service.start_async()


@app.on_event("shutdown")
def _shutdown() -> None:
    worker_service.shutdown()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/reference-video/{word}")
def reference_video(word: str) -> FileResponse:
    try:
        path = _reference_video_path(word)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown reference video: {word}") from None
    return FileResponse(path, media_type="video/mp4", filename=path.name)


@app.get("/api/status")
def api_status() -> Dict[str, Any]:
    return {
        "service": "signLanguage scoring MVP",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "prototype similarity only; not a calibrated real-user score",
        "template_root": str(TEMPLATE_ROOT),
        "output_root": str(OUTPUT_ROOT),
        "semantic_profile_json": str(SEMANTIC_PROFILE_JSON),
        "templates": _list_templates(),
        "worker": worker_service.snapshot(),
    }


@app.get("/api/templates")
def api_templates() -> Dict[str, Any]:
    return {"templates": _list_templates()}


@app.post("/api/score")
def api_score(request: ScoreRequest) -> Dict[str, Any]:
    if not request.frames:
        raise HTTPException(status_code=400, detail="frames is empty")
    if len(request.frames) > 90:
        raise HTTPException(status_code=400, detail="too many frames; keep one request under 90 frames")
    try:
        standard_json = _template_path(request.target_word)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"unknown template word: {request.target_word}") from None

    request_id = f"web_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    result_dir = OUTPUT_ROOT / request_id
    holistic_dir = result_dir / "holistic"
    holistic_dir.mkdir(parents=True, exist_ok=True)
    frame_indices = request.frame_indices or list(range(len(request.frames)))
    if len(frame_indices) != len(request.frames):
        raise HTTPException(status_code=400, detail="frame_indices and frames length mismatch")

    worker_payload = {
        "cmd": "process_frames",
        "request_id": request_id,
        "video_stem": f"user_{request.target_word}_{request_id}",
        "fps": float(request.fps),
        "total_frames": len(request.frames),
        "frame_indices": [int(idx) for idx in frame_indices],
        "frames": request.frames,
        "result_dir": str(holistic_dir),
    }

    started = time.perf_counter()
    try:
        worker_response = worker_service.request(worker_payload, timeout_sec=request.wait_for_ready_sec)
        result_file = worker_response.get("result_file")
        if not result_file:
            raise RuntimeError("worker response does not include result_file")
        standard = load_sequence(standard_json, requested_mode="landmark")
        query = load_sequence(Path(result_file), requested_mode="landmark")
        score_result = run_pair(standard, query)
    except TimeoutError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    total_sec = round(time.perf_counter() - started, 3)
    score_payload = {
        "request_id": request_id,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "claim_policy": "prototype sanity check only; no calibrated real-user score or pass/fail threshold",
        "target_word": request.target_word,
        "standard_json": str(standard_json),
        "query_json": str(result_file),
        "duration_sec": request.duration_sec,
        "capture_fps": request.fps,
        "frame_count": len(request.frames),
        "worker": {
            "input_mode": worker_response.get("input_mode"),
            "ingest_sec": worker_response.get("ingest_sec"),
            "holistic_eval_sec": worker_response.get("holistic_eval_sec"),
            "request_total_sec": worker_response.get("request_total_sec"),
            "samples": worker_response.get("samples"),
        },
        "timing": {
            "api_total_sec": total_sec,
        },
        "score": {
            "prototype_score": score_result["prototype_score"],
            "dtw_distance": score_result["dtw_distance"],
            "normalized_distance": score_result["normalized_distance"],
            "path_length": score_result["path_length"],
            "sequence_penalty": score_result["sequence_penalty"],
            "group_mean_distance": score_result["group_mean_distance"],
            "worst_alignment_points": score_result["worst_alignment_points"][:5],
            "semantic_profile": score_result.get("semantic_profile"),
        },
        "artifacts": {
            "result_dir": str(result_dir),
            "holistic_json": str(result_file),
            "scoring_json": str(result_dir / "scoring_result.json"),
            "worker_stderr_log": worker_service.snapshot().get("stderr_log"),
        },
    }
    (result_dir / "scoring_result.json").write_text(
        json.dumps(score_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return score_payload


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5080, log_level="info")


if __name__ == "__main__":
    main()
