import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { BASE_LOOK, CutOut, Defs, FPS, Hi, Look, LookCtx, OSWALD, PaperBG, PaperOverlay, Scene, C, loopPath, Draw, Arrow, toReal } from "./ui";
import { S1, S2, S3, S4, SMap, STank, STally, SCrack, SPuff, SStress, SDoc, SRound, SEnd } from "./scenes";
import { CometArt, WindowArt } from "./art";
import laurenMap from "./lauren-map.json";

export const DURATION = 60;   // Andrew version, seconds (voice ends at 58.5 s)
export const DURATION_LAUREN = 68; // Lauren (ElevenLabs) version, voice ends at 66.8 s
export const LAUREN: Look = { real: laurenMap.real, base: laurenMap.base, rich: true, dy: 70 };
export const OV = 0.12;       // scenes overlap a little so the slide-out / slide-in reads as one move

// scene boundaries on the base (Andrew) timeline
export const SCENES: [number, number, React.FC<{ s: number }>][] = [
  [0, 3.0, S1], [3.0, 4.9, S2], [4.9, 11.0, S3], [11.0, 13.4, S4], [13.4, 22.4, SMap],
  [22.4, 28.6, STank], [28.6, 30.4, STally], [30.4, 34.0, SCrack], [34.0, 40.0, SPuff],
  [40.0, 46.8, SStress], [46.8, 51.4, SDoc], [51.4, 53.9, SRound], [53.9, 60, SEnd],
];

const Body: React.FC<{ look: Look; total: number }> = ({ look, total }) => (
  <LookCtx.Provider value={look}>
    <AbsoluteFill>
      <Defs />
      <PaperBG />
      {SCENES.map(([a, b, Comp], i) => {
        const last = i === SCENES.length - 1;
        const s = Math.max(0, toReal(look, a) - OV), e = last ? total : Math.min(total, toReal(look, b) + OV);
        return (
          <Sequence key={i} from={Math.round(s * FPS)} durationInFrames={Math.round((e - s) * FPS)}>
            <Scene len={e - s} push={last ? 0 : 0.05}>
              <Comp s={s} />
            </Scene>
          </Sequence>
        );
      })}
      <PaperOverlay />
    </AbsoluteFill>
  </LookCtx.Provider>
);

export const WindowShort: React.FC = () => <Body look={BASE_LOOK} total={DURATION} />;
export const WindowLauren: React.FC = () => <Body look={LAUREN} total={DURATION_LAUREN} />;

/* ---------- thumbnails (1080 x 1920 stills) ---------- */
const ThumbText: React.FC<{ l1: string; l2: string; s2?: number }> = ({ l1, l2, s2 = 210 }) => (
  <div style={{ position: "absolute", top: 120, left: 0, right: 0, textAlign: "center", fontFamily: OSWALD, fontWeight: 700, textTransform: "uppercase", lineHeight: 1.0 }}>
    <div style={{ fontSize: 150, color: C.ink }}>{l1}</div>
    <div style={{ fontSize: s2, color: C.ink, transform: "rotate(-2deg)", whiteSpace: "nowrap" }}><Hi p={1}>{l2}</Hi></div>
  </div>
);

const ThumbAInner: React.FC = () => (
  <AbsoluteFill>
    <Defs /><PaperBG />
    <ThumbText l1="This shape" l2="was deadly" s2={170} />
    <div style={{ position: "absolute", left: 120, top: 640, width: 520, height: 720, transform: "rotate(-4deg)" }}>
      <CutOut tape style={{ width: "100%", height: "100%" }}><WindowArt square drift={60} /></CutOut>
    </div>
    <div style={{ position: "absolute", left: 700, top: 1010, width: 260, height: 364, transform: "rotate(5deg)" }}>
      <CutOut style={{ width: "100%", height: "100%" }}><WindowArt drift={160} /></CutOut>
    </div>
    <svg viewBox="0 0 1080 1920" style={{ position: "absolute", inset: 0, overflow: "visible" }}>
      <Draw d={loopPath(575, 715, 140, 125)} p={1} w={16} />
      <Arrow a={[930, 640]} b={[730, 700]} bend={-60} p={1} w={16} />
      <path d="M 770 960 L 820 1000 L 920 900" fill="none" stroke={C.green} strokeWidth={22} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
    <PaperOverlay />
  </AbsoluteFill>
);

const ThumbBInner: React.FC = () => (
  <AbsoluteFill>
    <Defs /><PaperBG />
    <ThumbText l1="Why not" l2="square?" />
    <div style={{ position: "absolute", left: -110, top: 820, transform: "rotate(-6deg)" }}>
      <CutOut tape><CometArt width={1300} uid="thb" /></CutOut>
    </div>
    <svg viewBox="0 0 1080 1920" style={{ position: "absolute", inset: 0, overflow: "visible" }}>
      <Draw d={loopPath(520, 985, 135, 95)} p={1} w={16} />
      <Arrow a={[880, 1330]} b={[630, 1080]} bend={70} p={1} w={16} />
    </svg>
    <div style={{ position: "absolute", left: 120, top: 1240, transform: "rotate(-5deg)", background: C.ink, color: C.yellow, fontFamily: OSWALD, fontWeight: 700, fontSize: 96, padding: "6px 34px", filter: "url(#shadow)" }}>1954</div>
    <PaperOverlay />
  </AbsoluteFill>
);

export const ThumbA: React.FC = () => <ThumbAInner />;
export const ThumbB: React.FC = () => <ThumbBInner />;
export const ThumbA2: React.FC = () => <LookCtx.Provider value={LAUREN}><ThumbAInner /></LookCtx.Provider>;
export const ThumbB2: React.FC = () => <LookCtx.Provider value={LAUREN}><ThumbBInner /></LookCtx.Provider>;
