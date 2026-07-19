from __future__ import annotations

from pathlib import Path
from threading import Lock
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.config import Settings, get_settings
from backend.pipeline import run_pipeline
from backend.utils.files import ensure_directory
from backend.utils.logging import configure_logging

BASE_SETTINGS = get_settings()
configure_logging(BASE_SETTINGS.log_level)
ensure_directory(BASE_SETTINGS.outputs_dir)
PIPELINE_LOCK = Lock()
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

app = FastAPI(
    title="FotoOwl Pipeline API",
    description="Upload images and a prompt to generate a Remotion video from the FotoOwl pipeline.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/artifacts", StaticFiles(directory=str(BASE_SETTINGS.outputs_dir)), name="artifacts")


class SampleRunRequest(BaseModel):
    prompt: str


def _build_run_settings(run_id: str) -> Settings:
    return BASE_SETTINGS.model_copy(
        update={
            "outputs_dir": BASE_SETTINGS.outputs_dir / "runs" / run_id,
        }
    )


def _artifact_path(run_id: str, filename: str) -> Path:
    return BASE_SETTINGS.outputs_dir / "runs" / run_id / filename


def _artifact_url(run_id: str, filename: str) -> str | None:
    path = _artifact_path(run_id=run_id, filename=filename)
    if not path.exists():
        return None
    return f"/artifacts/runs/{run_id}/{filename}"


def _serialize_run(run_id: str, final_state) -> dict[str, object]:
    return {
        "run_id": run_id,
        "status": final_state.render_status,
        "failure_reason": final_state.failure_reason,
        "pipeline_logs": final_state.pipeline_logs,
        "selected_images": [str(path) for path in final_state.selected_images],
        "artifacts": {
            "video_intent": _artifact_url(run_id, "video_intent.json"),
            "analysis": _artifact_url(run_id, "analysis.json"),
            "storyboard": _artifact_url(run_id, "storyboard.json"),
            "generated_script": _artifact_url(run_id, "generated_script.tsx"),
            "compile_log": _artifact_url(run_id, "compile_log.txt"),
            "render_log": _artifact_url(run_id, "render_log.txt"),
            "pipeline_state": _artifact_url(run_id, "pipeline_state.json"),
            "final_video": _artifact_url(run_id, "final_video.mp4"),
        },
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "model_provider": BASE_SETTINGS.llm_provider,
        "text_model": BASE_SETTINGS.text_model,
        "vision_model": BASE_SETTINGS.vision_model,
    }


@app.post("/run-sample")
def run_sample(request: SampleRunRequest) -> dict[str, object]:
    input_dir = BASE_SETTINGS.sample_images_dir
    if not input_dir.exists():
        raise HTTPException(status_code=404, detail="Sample images directory is missing.")
    if not PIPELINE_LOCK.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="A pipeline run is already in progress.")
    run_id = uuid4().hex[:12]
    try:
        settings = _build_run_settings(run_id)
        final_state = run_pipeline(settings=settings, input_dir=input_dir, prompt=request.prompt)
    finally:
        PIPELINE_LOCK.release()
    return _serialize_run(run_id=run_id, final_state=final_state)


@app.post("/run-upload")
async def run_upload(
    prompt: str = Form(...),
    files: list[UploadFile] = File(...),
) -> dict[str, object]:
    if not files:
        raise HTTPException(status_code=400, detail="At least one image is required.")
    if not PIPELINE_LOCK.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="A pipeline run is already in progress.")

    run_id = uuid4().hex[:12]
    input_dir = BASE_SETTINGS.outputs_dir / "runs" / run_id / "inputs"
    ensure_directory(input_dir)
    saved_images = 0

    try:
        for upload in files:
            filename = Path(upload.filename or "upload.jpg").name
            suffix = Path(filename).suffix.lower()
            if suffix not in IMAGE_EXTENSIONS:
                continue
            target_path = input_dir / filename
            target_path.write_bytes(await upload.read())
            saved_images += 1
        if saved_images == 0:
            raise HTTPException(status_code=400, detail="No supported image files were uploaded.")

        settings = _build_run_settings(run_id)
        final_state = run_pipeline(settings=settings, input_dir=input_dir, prompt=prompt)
    finally:
        PIPELINE_LOCK.release()

    response = _serialize_run(run_id=run_id, final_state=final_state)
    response["uploaded_images"] = saved_images
    return response
