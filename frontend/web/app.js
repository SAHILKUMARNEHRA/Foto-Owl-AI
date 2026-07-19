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
localStorage.removeItem("fotoOwlApiBase");
connectionBadge.textContent = isLocalFrontend ? "Local backend" : "Connected to Render";

const setStatus = (label, tone, detail) => {
  statusBadge.textContent = label;
  statusBadge.className = `badge ${tone}`;
  statusOutput.textContent = detail;
};

const getApiBase = () => {
  return DEFAULT_API_BASE.replace(/\/+$/, "");
};

const renderArtifacts = (apiBase, payload) => {
  const artifactEntries = Object.entries(payload.artifacts || {}).filter(([, value]) => Boolean(value));
  if (!artifactEntries.length) {
    artifactsContainer.className = "artifacts empty";
    artifactsContainer.textContent = "No artifacts were returned.";
    return;
  }

  artifactsContainer.className = "artifacts";
  artifactsContainer.innerHTML = artifactEntries
    .map(([name, relativeUrl]) => {
      const url = `${apiBase}${relativeUrl}`;
      return `<a class="artifact-link" href="${url}" target="_blank" rel="noreferrer">${name}</a>`;
    })
    .join("");
};

const runRequest = async (requestFactory) => {
  const apiBase = getApiBase();
  const prompt = promptInput.value.trim();
  if (!prompt) {
    setStatus("Error", "error", "Enter a creative prompt before running the pipeline.");
    return;
  }

  setStatus("Running", "running", "Pipeline is running. This can take a while during image analysis and rendering.");
  artifactsContainer.className = "artifacts empty";
  artifactsContainer.textContent = "Generating artifacts...";

  try {
    const response = await requestFactory(apiBase, prompt);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Pipeline request failed.");
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
    renderArtifacts(apiBase, payload);
  } catch (error) {
    setStatus("Error", "error", error instanceof Error ? error.message : "Unexpected error.");
    artifactsContainer.className = "artifacts empty";
    artifactsContainer.textContent = "Artifacts unavailable because the request failed.";
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

runUploadButton.addEventListener("click", () => {
  if (!filesInput.files || filesInput.files.length === 0) {
    setStatus("Error", "error", "Select at least one image before running an uploaded job.");
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
