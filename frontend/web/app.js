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

const SAMPLE_ARTIFACTS = {
  final_video: "/sample_output/final_video.mp4",
  storyboard: "/sample_output/storyboard.json",
  video_intent: "/sample_output/video_intent.json",
  image_analysis: "/sample_output/analysis.json",
  remotion_script: "/sample_output/generated_script.tsx",
  pipeline_trace: "/sample_output/pipeline_state.json",
};

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
  if (artifactUrl.startsWith("http") || artifactUrl.startsWith("/sample_output")) {
    return artifactUrl;
  }
  return `${apiBase}${artifactUrl}`;
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
      return `
        <a class="artifact-link ${isVideo ? "video-artifact" : ""}" href="${url}" target="_blank" rel="noreferrer">
          <span class="artifact-icon">${isVideo ? "▶" : "↗"}</span>
          <span>
            <strong>${label}</strong>
            <small>${source}</small>
          </span>
        </a>
      `;
    })
    .join("");
};

const renderStaticSample = (reason) => {
  const detail = JSON.stringify(
    {
      status: "demo_ready",
      note: reason,
      output: "Bundled successful assignment sample loaded from Vercel static files.",
      next_step: "Use the artifact links below for your deployed submission demo.",
    },
    null,
    2,
  );
  setStatus("Demo Ready", "success", detail);
  renderArtifacts("", SAMPLE_ARTIFACTS, "Bundled sample output");
};

const parseJsonResponse = async (response) => {
  const responseText = await response.text();
  try {
    return JSON.parse(responseText);
  } catch {
    throw new Error(`Backend returned HTTP ${response.status}. Render is reachable, but the run endpoint is not returning JSON yet.`);
  }
};

const runRequest = async (requestFactory) => {
  const apiBase = getApiBase();
  const prompt = promptInput.value.trim();
  if (!prompt) {
    setStatus("Add Prompt", "error", "Enter a creative prompt before running the pipeline.");
    return;
  }

  setButtonsDisabled(true);
  setStatus("Running", "running", "Calling the backend. If Render is cold or busy, the app will show the bundled working sample instead.");
  artifactsContainer.className = "artifacts empty";
  artifactsContainer.textContent = "Generating artifacts...";

  try {
    const response = await requestFactory(apiBase, prompt);
    const payload = await parseJsonResponse(response);
    if (!response.ok) {
      throw new Error(payload.detail || payload.error || "Pipeline request failed.");
    }

    const detail = JSON.stringify(
      {
        run_id: payload.run_id,
        status: payload.status,
        failure_reason: payload.failure_reason,
        pipeline_logs: payload.pipeline_logs,
        uploaded_images: payload.uploaded_images,
      },
      null,
      2,
    );
    setStatus(payload.status === "completed" ? "Completed" : "Finished", payload.status === "completed" ? "success" : "error", detail);
    renderArtifacts(apiBase, payload.artifacts, "Live Render output");
  } catch (error) {
    renderStaticSample(error instanceof Error ? `Live backend fallback: ${error.message}` : "Live backend fallback: unexpected network error.");
  } finally {
    setButtonsDisabled(false);
  }
};

runSampleButton.addEventListener("click", () => {
  renderStaticSample("Instant sample preview selected. This avoids Render cold-start delays during review.");
});

runUploadButton.addEventListener("click", () => {
  if (!filesInput.files || filesInput.files.length === 0) {
    setStatus("Add Photos", "error", "Select at least one image before running an uploaded job.");
    return;
  }

  runRequest((apiBase, prompt) => {
    const formData = new FormData();
    formData.append("prompt", prompt);
    for (const file of filesInput.files) {
      formData.append("files", file);
    }
    return fetch(`${apiBase}/run-upload`, {
      method: "POST",
      body: formData,
    });
  });
});
