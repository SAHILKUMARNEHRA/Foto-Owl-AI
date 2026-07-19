import React from "react";
import {
  AbsoluteFill,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

type Scene = {
  startFrame: number;
  durationInFrames: number;
  caption: string;
  transition: string;
  image: string;
  animation: string;
  reason: string;
};

const scenes: Scene[] = [
  {
    "startFrame": 0,
    "durationInFrames": 90,
    "caption": "The day opens with quiet anticipation.",
    "transition": "Fade",
    "image": "generated_assets/scene_00.jpg",
    "animation": "Gentle Zoom In",
    "reason": "Selected for its warm and celebratory mood and narrative relevance."
  },
  {
    "startFrame": 90,
    "durationInFrames": 90,
    "caption": "Warm smiles gather into a shared story.",
    "transition": "Cross Dissolve",
    "image": "generated_assets/scene_01.jpg",
    "animation": "Slow Pan",
    "reason": "Selected for its warm and celebratory mood and narrative relevance."
  },
  {
    "startFrame": 180,
    "durationInFrames": 90,
    "caption": "Details and faces become lasting memories.",
    "transition": "Fade",
    "image": "generated_assets/scene_02.jpg",
    "animation": "Gentle Zoom In",
    "reason": "Selected for its warm and celebratory mood and narrative relevance."
  },
  {
    "startFrame": 270,
    "durationInFrames": 90,
    "caption": "The celebration settles into a graceful finale.",
    "transition": "Cross Dissolve",
    "image": "generated_assets/scene_03.jpg",
    "animation": "Slow Pan",
    "reason": "Selected for its warm and celebratory mood and narrative relevance."
  },
  {
    "startFrame": 360,
    "durationInFrames": 90,
    "caption": "The day opens with quiet anticipation.",
    "transition": "Fade",
    "image": "generated_assets/scene_04.jpg",
    "animation": "Gentle Zoom In",
    "reason": "Selected for its warm and celebratory mood and narrative relevance."
  },
  {
    "startFrame": 450,
    "durationInFrames": 90,
    "caption": "Warm smiles gather into a shared story.",
    "transition": "Cross Dissolve",
    "image": "generated_assets/scene_05.jpg",
    "animation": "Slow Pan",
    "reason": "Selected for its warm and celebratory mood and narrative relevance."
  },
  {
    "startFrame": 540,
    "durationInFrames": 90,
    "caption": "Details and faces become lasting memories.",
    "transition": "Fade",
    "image": "generated_assets/scene_06.jpg",
    "animation": "Gentle Zoom In",
    "reason": "Selected for its warm and celebratory mood and narrative relevance."
  },
  {
    "startFrame": 630,
    "durationInFrames": 90,
    "caption": "The celebration settles into a graceful finale.",
    "transition": "Cross Dissolve",
    "image": "generated_assets/scene_07.jpg",
    "animation": "Slow Pan",
    "reason": "Selected for its warm and celebratory mood and narrative relevance."
  }
];

export const VIDEO_FPS = 30;
export const VIDEO_WIDTH = 1920;
export const VIDEO_HEIGHT = 1080;
export const VIDEO_DURATION_IN_FRAMES = 720;
const TRANSITION_FRAMES = 24;
const OVERLAY_OPACITY = 0.22;
const CAPTION_FONT_SCALE = 1.0;
const GRADIENT_STRENGTH = 0.34;
const TITLE_TREATMENT = "Elegant cinematic title treatment";
const MOTION_BIAS = "gentle";
const COLOR_PALETTE = "warm golden tones";

const sceneTransform = (frame: number, durationInFrames: number, animation: string): string => {
  const entrance = spring({frame, fps: VIDEO_FPS, config: {damping: 16}});
  const exitStart = Math.max(durationInFrames - TRANSITION_FRAMES, 1);
  const drift = interpolate(frame, [0, durationInFrames], [0, animation.includes("left") ? -40 : 40], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scaleStart = animation.toLowerCase().includes("zoom out") ? 1.12 : 1.02;
  const scaleEnd = animation.toLowerCase().includes("zoom out") ? 1.0 : 1.12;
  const scale = interpolate(frame, [0, durationInFrames], [scaleStart, scaleEnd], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(frame, [0, TRANSITION_FRAMES, exitStart, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return `translate3d(${drift}px, 0, 0) scale(${scale * Math.max(entrance, 0.85)})`;
};

const CaptionBlock: React.FC<{caption: string; frame: number; durationInFrames: number}> = ({
  caption,
  frame,
  durationInFrames,
}) => {
  const opacity = interpolate(frame, [0, 8, durationInFrames - 8, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const translateY = interpolate(frame, [0, 15], [20, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute",
        left: 96,
        right: 96,
        bottom: 84,
        opacity,
        transform: `translateY(${translateY}px)`,
      }}
    >
      <div
        style={{
          maxWidth: 1240,
          padding: "22px 28px",
          borderRadius: 24,
          backgroundColor: `rgba(0, 0, 0, ${OVERLAY_OPACITY})`,
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
        {caption}
      </div>
    </div>
  );
};

const SceneView: React.FC<{scene: Scene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, TRANSITION_FRAMES, scene.durationInFrames], [0, 1, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ opacity }}>
      <Img
        src={staticFile(scene.image)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: sceneTransform(frame, scene.durationInFrames, scene.animation + MOTION_BIAS),
        }}
      />
      <AbsoluteFill
        style={{ background: `linear-gradient(180deg, rgba(0, 0, 0, 0.12), rgba(0, 0, 0, ${GRADIENT_STRENGTH }}))`,
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
          {TITLE_TREATMENT} | {COLOR_PALETTE}
        </div>
        <CaptionBlock caption={scene.caption} frame={frame} durationInFrames={scene.durationInFrames} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const GeneratedVideo: React.FC = () => {
  const {fps} = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#050505" }}>
      {scenes.map((scene) => (
        <Sequence key={`${scene.startFrame}-${scene.image}`} from={scene.startFrame} durationInFrames={scene.durationInFrames}>
          <SceneView scene={scene} />
        </Sequence>
      ))}
      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          padding: 32,
          color: "rgba(255, 255, 255, 0.55)",
          fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif",
          fontSize: 18,
        }}
      >
        <div>Rendered at {fps} fps</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export default GeneratedVideo;
