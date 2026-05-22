#!/usr/bin/env python3
"""V2 frontend shell for the signLanguage scoring MVP.

This version keeps the original 5080 service as the single shared Holistic
scoring backend. Port 5081 serves the revised frontend and local reference
videos, while /api/status, /api/templates, and /api/score are proxied to 5080.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib import error as urlerror
from urllib import request as urlrequest

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import backend as base


STATIC_DIR = Path(__file__).resolve().parent / "static_v2"
OUTPUT_ROOT = base.WORK_DIR / "generated/web_scoring_mvp_v2"
DEMO_VIDEO_ROOT = base.REPO_ROOT / "data/Demo词汇视频/Demo词汇视频"
PORT = 5081
SHARED_BACKEND_BASE = "http://127.0.0.1:5080"

app = FastAPI(title="signLanguage Scoring MVP V2", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _reference_video_path(word: str) -> Path:
    direct = DEMO_VIDEO_ROOT / f"{word}.mp4"
    if direct.exists():
        return direct
    matches = sorted(DEMO_VIDEO_ROOT.glob(f"{word}.*"))
    for item in matches:
        if item.suffix.lower() == ".mp4":
            return item
    raise KeyError(word)


def _list_templates_v2() -> List[Dict[str, Any]]:
    templates = _proxy_json("GET", "/api/templates").get("templates", [])
    for item in templates:
        word = item["word"]
        try:
            path = _reference_video_path(word)
            item["reference_video"] = str(path)
            item["reference_video_url"] = f"/api/reference-video/{word}"
        except KeyError:
            item["reference_video"] = None
            item["reference_video_url"] = None
    return templates


@app.on_event("startup")
def _startup() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    base.LOG_DIR.mkdir(parents=True, exist_ok=True)


@app.on_event("shutdown")
def _shutdown() -> None:
    return None


def _proxy_json(method: str, path: str, payload: Dict[str, Any] | None = None, timeout: float = 900.0) -> Dict[str, Any]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urlrequest.Request(
        f"{SHARED_BACKEND_BASE}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urlerror.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
        except Exception:
            detail = exc.reason
        raise HTTPException(status_code=exc.code, detail=detail) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"shared backend unavailable: {exc}") from exc


def _model_to_dict(model: base.ScoreRequest) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


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
    status = _proxy_json("GET", "/api/status")
    status["service"] = "signLanguage scoring MVP V2"
    status["generated_at"] = datetime.now().isoformat(timespec="seconds")
    status["demo_video_root"] = str(DEMO_VIDEO_ROOT)
    status["output_root"] = str(OUTPUT_ROOT)
    status["templates"] = _list_templates_v2()
    status["ui_version"] = "v2_reference_video"
    status["port"] = PORT
    status["shared_backend"] = SHARED_BACKEND_BASE
    status["frontend_role"] = "static_frontend_and_proxy_only"
    return status


@app.get("/api/templates")
def api_templates() -> Dict[str, Any]:
    return {"templates": _list_templates_v2()}


@app.post("/api/score")
def api_score(request: base.ScoreRequest) -> Dict[str, Any]:
    result = _proxy_json("POST", "/api/score", _model_to_dict(request), timeout=request.wait_for_ready_sec + 120.0)
    result["frontend_proxy"] = {
        "version": "v2_reference_video",
        "port": PORT,
        "shared_backend": SHARED_BACKEND_BASE,
    }
    return result


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")


if __name__ == "__main__":
    main()
