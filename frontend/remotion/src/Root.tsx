import React from "react";
import {Composition} from "remotion";
import GeneratedVideo, {
  VIDEO_DURATION_IN_FRAMES,
  VIDEO_FPS,
  VIDEO_HEIGHT,
  VIDEO_WIDTH,
} from "./generated/GeneratedVideo";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="FotoOwlGenerated"
      component={GeneratedVideo}
      durationInFrames={VIDEO_DURATION_IN_FRAMES}
      fps={VIDEO_FPS}
      width={VIDEO_WIDTH}
      height={VIDEO_HEIGHT}
    />
  );
};
