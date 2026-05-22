const state = {
  stream: null,
  templates: [],
  busy: false,
  referenceVisible: false,
};

const els = {
  workerStatus: document.getElementById("workerStatus"),
  cameraStatus: document.getElementById("cameraStatus"),
  mediaRow: document.getElementById("mediaRow"),
  referenceToggle: document.getElementById("referenceToggle"),
  preview: document.getElementById("preview"),
  countdownOverlay: document.getElementById("countdownOverlay"),
  countdownValue: document.getElementById("countdownValue"),
  referenceVideo: document.getElementById("referenceVideo"),
  referenceLabel: document.getElementById("referenceLabel"),
  canvas: document.getElementById("captureCanvas"),
  targetWord: document.getElementById("targetWord"),
  durationSec: document.getElementById("durationSec"),
  captureFps: document.getElementById("captureFps"),
  frameWidth: document.getElementById("frameWidth"),
  cameraBtn: document.getElementById("cameraBtn"),
  recordBtn: document.getElementById("recordBtn"),
  progressBar: document.getElementById("progressBar"),
  captureLog: document.getElementById("captureLog"),
  scoreRing: document.getElementById("scoreRing"),
  scoreValue: document.getElementById("scoreValue"),
  resultTitle: document.getElementById("resultTitle"),
  resultNote: document.getElementById("resultNote"),
  dtwDistance: document.getElementById("dtwDistance"),
  normDistance: document.getElementById("normDistance"),
  workerTime: document.getElementById("workerTime"),
  frameCount: document.getElementById("frameCount"),
  groupMetrics: document.getElementById("groupMetrics"),
  penaltyMetrics: document.getElementById("penaltyMetrics"),
};

function setLog(text) {
  els.captureLog.textContent = text;
}

function formatNumber(value, digits = 3) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return Number(value).toFixed(digits);
}

async function refreshStatus() {
  try {
    const resp = await fetch("/api/status");
    const data = await resp.json();
    const worker = data.worker || {};
    els.workerStatus.classList.remove("ready", "error");
    if (worker.status === "ready") {
      const init = worker.ready_payload?.holistic_init_sec;
      els.workerStatus.textContent = init ? `后端已就绪 · init ${init}s` : "后端已就绪";
      els.workerStatus.classList.add("ready");
      els.recordBtn.disabled = !state.stream || state.busy;
    } else if (worker.status === "error") {
      els.workerStatus.textContent = "后端错误";
      els.workerStatus.classList.add("error");
      els.recordBtn.disabled = true;
    } else {
      els.workerStatus.textContent = "Holistic 初始化中";
      els.recordBtn.disabled = true;
    }
    if (!state.templates.length && Array.isArray(data.templates)) {
      populateTemplates(data.templates);
    } else if (state.templates.length) {
      updateReferenceVideo();
    }
  } catch (err) {
    els.workerStatus.textContent = "无法连接后端";
    els.workerStatus.classList.add("error");
    els.recordBtn.disabled = true;
  }
}

function populateTemplates(templates) {
  state.templates = templates;
  els.targetWord.innerHTML = "";
  for (const item of templates) {
    const option = document.createElement("option");
    option.value = item.word;
    option.textContent = `${item.label} (${item.records ?? "?"}帧)`;
    if (item.word === "花") option.selected = true;
    els.targetWord.appendChild(option);
  }
  updateReferenceVideo();
}

function updateReferenceVideo() {
  const word = els.targetWord.value;
  const item = state.templates.find((row) => row.word === word);
  els.referenceLabel.textContent = word || "--";
  if (!state.referenceVisible || !item?.reference_video_url) {
    els.referenceVideo.removeAttribute("src");
    els.referenceVideo.load();
    return;
  }
  const nextSrc = item.reference_video_url;
  if (!els.referenceVideo.src.endsWith(encodeURI(nextSrc))) {
    els.referenceVideo.src = nextSrc;
    els.referenceVideo.load();
  }
}

function setReferenceVisible(visible) {
  state.referenceVisible = Boolean(visible);
  els.mediaRow.classList.toggle("reference-hidden", !state.referenceVisible);
  els.referenceToggle.textContent = state.referenceVisible ? "隐藏参考" : "查看参考";
  els.referenceToggle.setAttribute("aria-expanded", state.referenceVisible ? "true" : "false");
  updateReferenceVideo();
}

async function openCamera() {
  try {
    if (state.stream) {
      closeCamera({ silent: true });
    }
    state.stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 960 },
        height: { ideal: 720 },
        facingMode: "user",
      },
      audio: false,
    });
    els.preview.srcObject = state.stream;
    els.cameraStatus.textContent = "摄像头已开启";
    els.cameraBtn.textContent = "关闭摄像头";
    setLog("摄像头已开启。保持身体、双手和肩肘完整入画后采集。");
    for (const track of state.stream.getTracks()) {
      track.addEventListener("ended", () => closeCamera({ silent: true }), { once: true });
    }
    await refreshStatus();
  } catch (err) {
    els.cameraStatus.textContent = "摄像头开启失败";
    setLog(`摄像头权限失败：${err.message || err}`);
  }
}

function closeCamera({ silent = false } = {}) {
  if (state.stream) {
    for (const track of state.stream.getTracks()) {
      track.stop();
    }
  }
  state.stream = null;
  els.preview.srcObject = null;
  els.countdownOverlay.classList.add("hidden");
  els.cameraStatus.textContent = "摄像头未开启";
  els.cameraBtn.textContent = "开启摄像头";
  els.recordBtn.disabled = true;
  if (!silent) {
    setLog("摄像头已关闭。需要测评时可再次开启。");
  }
}

async function toggleCamera() {
  if (state.busy) {
    setLog("正在采集或打分，暂不关闭摄像头。");
    return;
  }
  if (state.stream) {
    closeCamera();
    return;
  }
  await openCamera();
}

function captureOneFrame(frameWidth) {
  const video = els.preview;
  const srcWidth = video.videoWidth || 640;
  const srcHeight = video.videoHeight || 480;
  const width = Math.max(240, Math.min(frameWidth, 960));
  const height = Math.round(width * (srcHeight / srcWidth));
  const canvas = els.canvas;
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext("2d", { willReadFrequently: false });
  ctx.drawImage(video, 0, 0, width, height);
  const dataUrl = canvas.toDataURL("image/jpeg", 0.82);
  return {
    image_format: "jpg",
    image_b64: dataUrl.split(",", 2)[1],
  };
}

async function recordFrames() {
  if (!state.stream || state.busy) return;
  state.busy = true;
  els.recordBtn.disabled = true;
  els.progressBar.style.width = "0%";
  setScorePending();

  const durationSec = Number(els.durationSec.value || 3);
  const fps = Number(els.captureFps.value || 5);
  const frameWidth = Number(els.frameWidth.value || 480);
  const targetFrames = Math.max(1, Math.round(durationSec * fps));
  const intervalMs = 1000 / fps;
  const frames = [];
  const frameIndices = [];

  try {
    await runCountdown(3);
  } catch (err) {
    state.busy = false;
    await refreshStatus();
    return;
  }

  setLog(`正在采集 ${durationSec}s，目标 ${targetFrames} 帧...`);
  for (let i = 0; i < targetFrames; i += 1) {
    const frame = captureOneFrame(frameWidth);
    frames.push(frame);
    frameIndices.push(i);
    els.progressBar.style.width = `${Math.round(((i + 1) / targetFrames) * 100)}%`;
    if (i + 1 < targetFrames) {
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
    }
  }

  setLog(`已采集 ${frames.length} 帧，正在发送到远端 Holistic 后端...`);
  try {
    const resp = await fetch("/api/score", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        target_word: els.targetWord.value,
        fps,
        duration_sec: durationSec,
        frame_indices: frameIndices,
        frames,
        wait_for_ready_sec: 600,
      }),
    });
    const data = await resp.json();
    if (!resp.ok) {
      throw new Error(data.detail || `HTTP ${resp.status}`);
    }
    renderResult(data);
    setLog(`打分完成。结果目录：${data.artifacts?.result_dir || "--"}`);
  } catch (err) {
    setLog(`打分失败：${err.message || err}`);
    els.resultTitle.textContent = "打分失败";
    els.resultNote.textContent = "查看后端日志或确认 Holistic worker 已就绪。";
  } finally {
    state.busy = false;
    await refreshStatus();
  }
}

async function runCountdown(seconds) {
  const total = Math.max(1, Number(seconds) || 3);
  els.countdownOverlay.classList.remove("hidden");
  for (let remaining = total; remaining >= 1; remaining -= 1) {
    els.countdownValue.textContent = String(remaining);
    setLog(`${remaining}s 后开始采集，请准备动作。`);
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }
  els.countdownValue.textContent = "开始";
  setLog("开始采集。");
  await new Promise((resolve) => setTimeout(resolve, 260));
  els.countdownOverlay.classList.add("hidden");
}

function setScorePending() {
  els.scoreValue.textContent = "--";
  els.scoreRing.style.background = "conic-gradient(var(--accent) 0deg, #e6ebf1 0deg)";
  els.resultTitle.textContent = "处理中";
  els.resultNote.textContent = "正在采集、识别并与目标模板做 DTW 对齐。";
  els.dtwDistance.textContent = "--";
  els.normDistance.textContent = "--";
  els.workerTime.textContent = "--";
  els.frameCount.textContent = "--";
}

function renderTable(tbody, entries) {
  tbody.innerHTML = "";
  for (const [key, value] of entries) {
    const tr = document.createElement("tr");
    const name = document.createElement("td");
    const val = document.createElement("td");
    name.textContent = key;
    val.textContent = typeof value === "number" ? formatNumber(value, 6) : String(value);
    tr.appendChild(name);
    tr.appendChild(val);
    tbody.appendChild(tr);
  }
}

function renderResult(data) {
  const score = data.score?.prototype_score ?? 0;
  const clamped = Math.max(0, Math.min(100, score));
  const degrees = (clamped / 100) * 360;
  els.scoreValue.textContent = formatNumber(score, 1);
  els.scoreRing.style.background = `conic-gradient(var(--accent) ${degrees}deg, #e6ebf1 ${degrees}deg)`;
  els.resultTitle.textContent = `${data.target_word} · 原型相似度`;
  els.resultNote.textContent = "该分数只用于当前 demo 模板的原型相似度检查，不是正式评分阈值。";
  els.dtwDistance.textContent = formatNumber(data.score?.dtw_distance, 5);
  els.normDistance.textContent = formatNumber(data.score?.normalized_distance, 5);
  els.workerTime.textContent = `${formatNumber(data.worker?.holistic_eval_sec, 3)}s`;
  els.frameCount.textContent = String(data.frame_count ?? "--");

  const groupEntries = Object.entries(data.score?.group_mean_distance || {});
  renderTable(els.groupMetrics, groupEntries.length ? groupEntries : [["暂无结果", "--"]]);

  const p = data.score?.sequence_penalty || {};
  renderTable(els.penaltyMetrics, [
    ["total_sequence_penalty", p.total_sequence_penalty],
    ["length_ratio", p.length_ratio],
    ["length_penalty", p.length_penalty],
    ["presence_penalty", p.presence_penalty],
    ["motion_penalty", p.motion_penalty],
    ["roughness_penalty", p.roughness_penalty],
    ["info_penalty", p.info_penalty],
    ["endpoint_penalty", p.endpoint_penalty],
  ]);
}

els.cameraBtn.addEventListener("click", toggleCamera);
els.recordBtn.addEventListener("click", recordFrames);
els.targetWord.addEventListener("change", updateReferenceVideo);
els.referenceToggle.addEventListener("click", () => setReferenceVisible(!state.referenceVisible));

setReferenceVisible(false);
refreshStatus();
setInterval(refreshStatus, 5000);
