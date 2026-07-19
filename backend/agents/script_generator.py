from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from backend.rag.retriever import RagRetriever
from backend.schemas.intent import VideoIntent
from backend.schemas.storyboard import Storyboard
from backend.utils.files import write_text
from backend.utils.ollama import TextModelClient


class ScriptGeneratorAgent:
    def __init__(
        self,
        model_client: TextModelClient,
        retriever: RagRetriever,
        frontend_dir: Path,
        generated_dir: Path,
        fps: int,
    ) -> None:
        self._model_client = model_client
        self._retriever = retriever
        self._frontend_dir = frontend_dir
        self._generated_dir = generated_dir
        self._fps = fps

    def generate(self, intent: VideoIntent, storyboard: Storyboard, outputs_dir: Path) -> str:
        doc_context = self._retriever.retrieve_remotion_docs(
            query=f"{intent.animation_style}\n{intent.transition_style}\ncaption overlays"
        )
        creative_plan = self._model_client.invoke_json(
            system_prompt=(
                "You produce small JSON style directives for a Remotion video generator. "
                "Return keys: title_treatment, caption_font_scale, overlay_opacity, "
                "motion_bias, transition_frames, gradient_strength."
            ),
            user_prompt=(
                f"Intent:\n{intent.model_dump_json(indent=2)}\n\n"
                f"Storyboard:\n{storyboard.model_dump_json(indent=2)}\n\n"
                f"Remotion references:\n{json.dumps(doc_context, indent=2)}"
            ),
        )
        script = self._build_script(
            intent=intent,
            storyboard=storyboard,
            creative_plan=creative_plan,
        )
        write_text(outputs_dir / "generated_script.tsx", script)
        write_text(self._generated_dir / "GeneratedVideo.tsx", script)
        return script

    def _build_script(
        self,
        intent: VideoIntent,
        storyboard: Storyboard,
        creative_plan: dict[str, object],
    ) -> str:
        public_assets_dir = self._frontend_dir / "public" / "generated_assets"
        public_assets_dir.mkdir(parents=True, exist_ok=True)
        scenes = []
        for scene in storyboard.scenes:
            asset_name = f"scene_{scene.scene_index:02d}{scene.image.suffix.lower()}"
            public_image_path = public_assets_dir / asset_name
            shutil.copy2(scene.image, public_image_path)
            scenes.append(
                {
                    "startFrame": int(round(scene.start_time * self._fps)),
                    "durationInFrames": max(1, int(round(scene.duration * self._fps))),
                    "caption": scene.caption,
                    "transition": scene.transition,
                    "image": f"generated_assets/{asset_name}",
                    "animation": scene.animation,
                    "reason": scene.reason,
                }
            )
        total_duration = sum(item["durationInFrames"] for item in scenes)
        transition_frames = int(creative_plan.get("transition_frames", 12))
        overlay_opacity = float(creative_plan.get("overlay_opacity", 0.35))
        caption_font_scale = float(creative_plan.get("caption_font_scale", 1.0))
        gradient_strength = float(creative_plan.get("gradient_strength", 0.6))
        title_treatment = json.dumps(str(creative_plan.get("title_treatment", storyboard.title)))
        motion_bias = json.dumps(str(creative_plan.get("motion_bias", intent.animation_style)))
        color_palette = json.dumps(intent.color_palette)
        scenes_json = json.dumps(scenes, indent=2)
        script = f"""import React from "react";
import {{
  AbsoluteFill,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
}} from "remotion";

type Scene = {{
  startFrame: number;
  durationInFrames: number;
  caption: string;
  transition: string;
  image: string;
  animation: string;
  reason: string;
}};

const scenes: Scene[] = {scenes_json};

export const VIDEO_FPS = {self._fps};
export const VIDEO_WIDTH = 1920;
export const VIDEO_HEIGHT = 1080;
export const VIDEO_DURATION_IN_FRAMES = {total_duration};
const TRANSITION_FRAMES = {transition_frames};
const OVERLAY_OPACITY = {overlay_opacity};
const CAPTION_FONT_SCALE = {caption_font_scale};
const GRADIENT_STRENGTH = {gradient_strength};
const TITLE_TREATMENT = {title_treatment};
const MOTION_BIAS = {motion_bias};
const COLOR_PALETTE = {color_palette};

const sceneTransform = (frame: number, durationInFrames: number, animation: string): string => {{
  const entrance = spring({{frame, fps: VIDEO_FPS, config: {{damping: 16}}}});
  const exitStart = Math.max(durationInFrames - TRANSITION_FRAMES, 1);
  const drift = interpolate(frame, [0, durationInFrames], [0, animation.includes("left") ? -40 : 40], {{
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  }});
  const scaleStart = animation.toLowerCase().includes("zoom out") ? 1.12 : 1.02;
  const scaleEnd = animation.toLowerCase().includes("zoom out") ? 1.0 : 1.12;
  const scale = interpolate(frame, [0, durationInFrames], [scaleStart, scaleEnd], {{
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  }});
  const opacity = interpolate(frame, [0, TRANSITION_FRAMES, exitStart, durationInFrames], [0, 1, 1, 0], {{
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  }});
  return `translate3d(${{drift}}px, 0, 0) scale(${{scale * Math.max(entrance, 0.85)}})`;
}};

const CaptionBlock: React.FC<{{caption: string; frame: number; durationInFrames: number}}> = ({{
  caption,
  frame,
  durationInFrames,
}}) => {{
  const opacity = interpolate(frame, [0, 8, durationInFrames - 8, durationInFrames], [0, 1, 1, 0], {{
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  }});
  const translateY = interpolate(frame, [0, 15], [20, 0], {{
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  }});
  return (
    <div
      style={{
        position: "absolute",
        left: 96,
        right: 96,
        bottom: 84,
        opacity,
        transform: `translateY(${{translateY}}px)`,
      }}
    >
      <div
        style={{
          maxWidth: 1240,
          padding: "22px 28px",
          borderRadius: 24,
          backgroundColor: `rgba(0, 0, 0, ${{OVERLAY_OPACITY}})`,
          backdropFilter: "blur(18px)",
          color: "white",
          fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
          fontSize: 42 * CAPTION_FONT_SCALE,
          fontWeight: 600,
          lineHeight: 1.18,
          letterSpacing: -0.8,
          boxShadow: "0 18px 50px rgba(0, 0, 0, 0.25)",
        }}
      >
        {{caption}}
      </div>
    </div>
  );
}};

const SceneView: React.FC<{{scene: Scene}}> = ({{scene}}) => {{
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, TRANSITION_FRAMES, scene.durationInFrames], [0, 1, 1], {{
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  }});

  return (
    <AbsoluteFill style={{ opacity }}>
      <Img
        src={{staticFile(scene.image)}}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: sceneTransform(frame, scene.durationInFrames, scene.animation + MOTION_BIAS),
        }}
      />
      <AbsoluteFill
        style={{
          background: `linear-gradient(180deg, rgba(0, 0, 0, 0.12), rgba(0, 0, 0, ${{GRADIENT_STRENGTH}}))`,
        }}
      />
      <AbsoluteFill
        style={{
          justifyContent: "space-between",
          padding: "64px 72px",
          color: "white",
          fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
        }}
      >
        <div
          style={{
            display: "inline-flex",
            alignSelf: "flex-start",
            padding: "12px 18px",
            borderRadius: 9999,
            backgroundColor: "rgba(255, 255, 255, 0.12)",
            fontSize: 24,
            fontWeight: 500,
            textTransform: "uppercase",
            letterSpacing: 1.4,
          }}
        >
          {{TITLE_TREATMENT}} | {{COLOR_PALETTE}}
        </div>
        <CaptionBlock caption={{scene.caption}} frame={{frame}} durationInFrames={{scene.durationInFrames}} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
}};

const GeneratedVideo: React.FC = () => {{
  const {{fps}} = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#050505" }}>
      {{scenes.map((scene) => (
        <Sequence key={{`${{scene.startFrame}}-${{scene.image}}`}} from={{scene.startFrame}} durationInFrames={{scene.durationInFrames}}>
          <SceneView scene={{scene}} />
        </Sequence>
      ))}}
      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          padding: 32,
          color: "rgba(255, 255, 255, 0.55)",
          fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
          fontSize: 18,
        }}
      >
        <div>Rendered at {{fps}} fps</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
}};

export default GeneratedVideo;
"""
        return self._normalize_jsx_style_braces(script)

    @staticmethod
    def _normalize_jsx_style_braces(script: str) -> str:
        script = re.sub(r"style=\{\s*([^{}\n][^\n]*?)\s*\}", r"style={{ \1 }}", script)
        script = re.sub(r"style=\{\n", "style={{\n", script)
        script = re.sub(r"(\n\s*)\}(\n\s*(?:>|/>))", r"\1}}\2", script)
        return script
