import "./index.css";
import { Composition, Still } from "remotion";
import { DURATION, DURATION_LAUREN, ThumbA, ThumbB, WindowShort } from "./window/WindowShort";
import { WideThumbA, WideThumbB, WindowLaurenWide } from "./window/wide";

// Example video: "Why Airplane Windows Are Never Square".
// For a new video, copy src/window to src/<slug>, rewrite its scenes, and register it here.
export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* 9:16 Short (Reels / Shorts / TikTok) */}
      <Composition id="WindowShort" component={WindowShort} durationInFrames={DURATION * 30} fps={30} width={1080} height={1920} />
      <Still id="WindowThumbA" component={ThumbA} width={1080} height={1920} />
      <Still id="WindowThumbB" component={ThumbB} width={1080} height={1920} />
      {/* 16:9 long-form re-layout of the same scenes (timed to a second narrator through lauren-map.json) */}
      <Composition id="WindowWide" component={WindowLaurenWide} durationInFrames={DURATION_LAUREN * 30} fps={30} width={1920} height={1080} />
      <Still id="WindowWideThumbA" component={WideThumbA} width={1920} height={1080} />
      <Still id="WindowWideThumbB" component={WideThumbB} width={1920} height={1080} />
    </>
  );
};
