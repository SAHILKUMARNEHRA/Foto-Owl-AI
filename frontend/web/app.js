const promptInput = document.querySelector("#prompt");
const filesInput = document.querySelector("#files");
const statusBadge = document.querySelector("#statusBadge");
const statusOutput = document.querySelector("#statusOutput");
const artifactsContainer = document.querySelector("#artifacts");
const runSampleButton = document.querySelector("#runSample");
const runUploadButton = document.querySelector("#runUpload");
const connectionBadge = document.querySelector("#connectionBadge");

const PRODUCTION_API_BASE = "https://foto-owl-ai.onrender.com";
const LOCAL_API_BASE = "http://localhost:8000";
const isLocalFrontend = ["localhost", "127.0.0.1"].includes(window.location.hostname);
const DEFAULT_API_BASE = isLocalFrontend ? LOCAL_API_BASE : PRODUCTION_API_BASE;
const MAX_UPLOAD_FILES = 4;
const MAX_UPLOAD_EDGE = 1600;
const JPEG_QUALITY = 0.82;
const POLL_INTERVAL_MS = 3000;
const MAX_POLL_ATTEMPTS = 180;

const ARTIFACT_LABELS = {
  final_video: "Final MP4 Video",
  storyboard: "Storyboard JSON",
  video_intent: "Video Intent JSON",
  image_analysis: "Image Analysis JSON",
  remotion_script: "Remotion Script",
  pipeline_trace: "Pipeline Trace",
};

localStorage.removeItem("fotoOwlApiBase");
connectionBadge.textContent = isLocalFrontend ? "Local backend mode" : "Render backend linked";

const setStatus = (label, tone, detail) => {
  statusBadge.textContent = label;
  statusBadge.className = `badge ${tone}`;
  statusOutput.textContent = detail;
};

const setButtonsDisabled = (isDisabled) => {
  runSampleButton.disabled = isDisabled;
  runUploadButton.disabled = isDisabled;
};

const getApiBase = () => DEFAULT_API_BASE.replace(/\/+$/, "");

const toAbsoluteArtifactUrl = (apiBase, artifactUrl) => {
  if (artifactUrl.startsWith("http")) {
    return artifactUrl;
  }
  return `${apiBase}${artifactUrl}`;
};

const formatBytes = (bytes) => {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const optimizeImage = async (file) => {
  if (!file.type.startsWith("image/")) {
    return file;
  }

  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, MAX_UPLOAD_EDGE / Math.max(bitmap.width, bitmap.height));
  if (scale === 1 && file.size < 1_500_000) {
    bitmap.close();
    return file;
  }

  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bitmap.width * scale);
  canvas.height = Math.round(bitmap.height * scale);
  const context = canvas.getContext("2d", {alpha: false});
  context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
  bitmap.close();

  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", JPEG_QUALITY));
  if (!blob || blob.size >= file.size) {
    return file;
  }

  const basename = file.name.replace(/\.[^.]+$/, "");
  return new File([blob], `${basename}.jpg`, {type: "image/jpeg", lastModified: Date.now()});
};

const optimizeUploads = async (files) => {
  const originalSize = files.reduce((sum, file) => sum + file.size, 0);
  const optimizedFiles = [];
  for (const file of files) {
    optimizedFiles.push(await optimizeImage(file));
  }
  const optimizedSize = optimizedFiles.reduce((sum, file) => sum + file.size, 0);
  return {optimizedFiles, originalSize, optimizedSize};
};

const renderArtifacts = (apiBase, artifacts, source = "Live pipeline output") => {
  const artifactEntries = Object.entries(artifacts || {}).filter(([, value]) => Boolean(value));
  if (!artifactEntries.length) {
    artifactsContainer.className = "artifacts empty";
    artifactsContainer.textContent = "No artifacts were returned.";
    return;
  }

  artifactsContainer.className = "artifacts";
  artifactsContainer.innerHTML = artifactEntries
    .map(([name, artifactUrl]) => {
      const url = toAbsoluteArtifactUrl(apiBase, artifactUrl);
      const label = ARTIFACT_LABELS[name] || name.replaceAll("_", " ");
      const isVideo = name === "final_video";
      if (isVideo) {
        return `
          <article class="artifact-link video-artifact video-card">
            <video controls preload="metadata" playsinline src="${url}"></video>
            <span>
              <strong>${label}</strong>
              <small>${source}. Streaming preview only; it will not auto-download.</small>
              <a class="text-link" href="${url}" target="_blank" rel="noreferrer">Open video in new tab</a>
            </span>
          </article>
        `;
      }
      return `
        <a class="artifact-link" href="${url}" target="_blank" rel="noreferrer">
          <span class="artifact-icon">↗</span>
          <span>
            <strong>${label}</strong>
            <small>${source}</small>
          </span>
        </a>
      `;
    })
    .join("");
};

const parseJsonResponse = async (response) => {
  const responseText = await response.text();
  try {
    return JSON.parse(responseText);
  } catch {
    throw new Error(`Backend returned HTTP ${response.status}. Render is reachable, but the run endpoint is not returning JSON yet.`);
  }
};

const delay = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

const renderRunPayload = (apiBase, payload) => {
  const fallbackProvider = payload.metadata?.fallback_provider;
  const detail = JSON.stringify(
    {
      run_id: payload.run_id,
      status: payload.status,
      failure_reason: payload.failure_reason,
      pipeline_logs: payload.pipeline_logs,
      uploaded_images: payload.uploaded_images,
      fallback_provider: fallbackProvider,
    },
    null,
    2,
  );
  setStatus(
    payload.status === "completed" ? (fallbackProvider ? "Completed Offline" : "Completed") : "Finished",
    payload.status === "completed" ? "success" : "error",
    detail,
  );
  renderArtifacts(apiBase, payload.artifacts, "Live Render output");
};

const pollRun = async (apiBase, runId) => {
  for (let attempt = 1; attempt <= MAX_POLL_ATTEMPTS; attempt += 1) {
    await delay(POLL_INTERVAL_MS);
    const response = await fetch(`${apiBase}/runs/${runId}`);
    const payload = await parseJsonResponse(response);
    if (!response.ok) {
      throw new Error(payload.detail || "Unable to read run status.");
    }

    if (payload.status === "queued" || payload.status === "running" || payload.status === "pending") {
      setStatus(
        payload.status === "queued" ? "Queued" : "Running",
        "running",
        JSON.stringify(
          {
            run_id: payload.run_id,
            status: payload.status,
            pipeline_logs: payload.pipeline_logs,
            message: "The backend is generating the real response. Keep this tab open.",
          },
          null,
          2,
        ),
      );
      continue;
    }

    return payload;
  }
  throw new Error("Run is still processing after several minutes. Open Render logs and check the backend worker.");
};

const runRequest = async (requestFactory) => {
  const apiBase = getApiBase();
  const prompt = promptInput.value.trim();
  if (!prompt) {
    setStatus("Add Prompt", "error", "Enter a creative prompt before running the pipeline.");
    setButtonsDisabled(false);
    return;
  }

  setButtonsDisabled(true);
  setStatus("Running", "running", "Calling the real backend. This may take time while Gemini analyzes images and Remotion renders the MP4.");
  artifactsContainer.className = "artifacts empty";
  artifactsContainer.textContent = "Generating live artifacts from the backend...";

  try {
    const response = await requestFactory(apiBase, prompt);
    let payload = await parseJsonResponse(response);
    if (!response.ok) {
      throw new Error(payload.detail || payload.error || "Pipeline request failed.");
    }

    if (payload.status === "queued" || payload.status === "running" || payload.status === "pending") {
      setStatus(
        "Queued",
        "running",
        JSON.stringify(
          {
            run_id: payload.run_id,
            status: payload.status,
            message: "Backend accepted the job. Polling for the real generated response now.",
          },
          null,
          2,
        ),
      );
      payload = await pollRun(apiBase, payload.run_id);
    }

    renderRunPayload(apiBase, payload);
  } catch (error) {
    setStatus("Backend Error", "error", error instanceof Error ? error.message : "Unexpected backend error.");
    artifactsContainer.className = "artifacts empty";
    artifactsContainer.textContent = "No demo fallback was used. Fix the backend error above and run again.";
  } finally {
    setButtonsDisabled(false);
  }
};

runSampleButton.addEventListener("click", () => {
  runRequest((apiBase, prompt) =>
    fetch(`${apiBase}/run-sample`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({prompt}),
    }),
  );
});

runUploadButton.addEventListener("click", async () => {
  if (!filesInput.files || filesInput.files.length === 0) {
    setStatus("Add Photos", "error", "Select at least one image before running an uploaded job.");
    return;
  }

  const selectedFiles = Array.from(filesInput.files).slice(0, MAX_UPLOAD_FILES);
  setButtonsDisabled(true);
  setStatus(
    "Optimizing",
    "running",
    `Compressing ${selectedFiles.length} image(s) before upload so Render receives a faster request and uses fewer Gemini vision credits.`,
  );
  let uploadBatch;
  try {
    uploadBatch = await optimizeUploads(selectedFiles);
  } catch {
    uploadBatch = {optimizedFiles: selectedFiles, originalSize: 0, optimizedSize: 0};
  }

  runRequest((apiBase, prompt) => {
    const formData = new FormData();
    formData.append("prompt", prompt);
    for (const file of uploadBatch.optimizedFiles) {
      formData.append("files", file);
    }
    const savedText =
      uploadBatch.originalSize > 0
        ? ` Optimized upload from ${formatBytes(uploadBatch.originalSize)} to ${formatBytes(uploadBatch.optimizedSize)}.`
        : "";
    setStatus("Uploading", "running", `Sending optimized images to the real backend.${savedText}`);
    return fetch(`${apiBase}/run-upload`, {
      method: "POST",
      body: formData,
    });
  });
});
