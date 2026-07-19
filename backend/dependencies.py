from __future__ import annotations

from dataclasses import dataclass

from backend.agents.compiler_fixer import CompilerFixerAgent
from backend.agents.image_analyzer import ImageAnalyzerAgent
from backend.agents.intent_parser import IntentParserAgent
from backend.agents.renderer import RendererAgent
from backend.agents.script_generator import ScriptGeneratorAgent
from backend.agents.storyboard_writer import StoryboardWriterAgent
from backend.compiler.compile import RemotionCompiler
from backend.config import Settings
from backend.rag.embeddings import LocalEmbeddingFunction
from backend.rag.retriever import RagRetriever
from backend.rag.seed import seed_vector_store
from backend.rag.vector_store import ChromaVectorStore
from backend.renderer.render import RemotionRenderer
from backend.utils.ollama import (
    GeminiTextClient,
    GeminiVisionClient,
    OfflineTextClient,
    OfflineVisionClient,
    OllamaTextClient,
    OllamaVisionClient,
)


@dataclass(slots=True)
class Container:
    intent_parser: IntentParserAgent
    image_analyzer: ImageAnalyzerAgent
    storyboard_writer: StoryboardWriterAgent
    script_generator: ScriptGeneratorAgent
    compiler: RemotionCompiler
    compiler_fixer: CompilerFixerAgent
    renderer: RendererAgent


def build_container(settings: Settings) -> Container:
    provider = settings.llm_provider.strip().lower()
    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY must be set when MODEL_PROVIDER=gemini.")
        text_client = GeminiTextClient(
            api_base_url=settings.gemini_api_base_url,
            api_key=settings.gemini_api_key,
            model=settings.text_model,
        )
        vision_client = GeminiVisionClient(
            api_base_url=settings.gemini_api_base_url,
            api_key=settings.gemini_api_key,
            model=settings.vision_model,
        )
    elif provider == "ollama":
        text_client = OllamaTextClient(base_url=settings.ollama_base_url, model=settings.text_model)
        vision_client = OllamaVisionClient(base_url=settings.ollama_base_url, model=settings.vision_model)
    elif provider == "offline":
        text_client = OfflineTextClient()
        vision_client = OfflineVisionClient()
    else:
        raise ValueError(f"Unsupported MODEL_PROVIDER: {settings.llm_provider}")
    embedding_function = LocalEmbeddingFunction(model_name=settings.embedding_model)
    vector_store = ChromaVectorStore(
        persist_directory=settings.vector_store_dir,
        embedding_function=embedding_function,
    )
    seed_vector_store(settings=settings, vector_store=vector_store)
    retriever = RagRetriever(vector_store=vector_store)
    compiler = RemotionCompiler(frontend_dir=settings.frontend_dir)
    renderer_service = RemotionRenderer(
        frontend_dir=settings.frontend_dir,
        codec=settings.render_codec,
        crf=settings.render_crf,
    )

    return Container(
        intent_parser=IntentParserAgent(model_client=text_client),
        image_analyzer=ImageAnalyzerAgent(
            vision_client=vision_client,
            max_selected_images=settings.max_selected_images,
        ),
        storyboard_writer=StoryboardWriterAgent(
            model_client=text_client,
            retriever=retriever,
            default_scene_duration_seconds=settings.default_scene_duration_seconds,
        ),
        script_generator=ScriptGeneratorAgent(
            model_client=text_client,
            retriever=retriever,
            frontend_dir=settings.frontend_dir,
            generated_dir=settings.remotion_generated_dir,
            fps=settings.default_fps,
        ),
        compiler=compiler,
        compiler_fixer=CompilerFixerAgent(model_client=text_client, retriever=retriever),
        renderer=RendererAgent(renderer=renderer_service, frontend_dir=settings.frontend_dir),
    )
