import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { Arrow, C, CutOut, Defs, Draw, FPS, GridFull, Hi, Look, LookCtx, OSWALD, PaperBG, PaperOverlay, Scene, loopPath, toReal } from "./ui";
import { CometArt, WindowArt } from "./art";
import { DURATION_LAUREN, LAUREN, OV, SCENES } from "./WindowShort";

/* 16:9 version. The scenes are drawn on a 1080 x 1920 canvas; here each one is re-framed:
   split = headline band on the left, art band on the right (the scene renders in both, each clipped to its band)
   zoom  = a camera window onto the portrait canvas, scaled to fill the frame height */
// hl / art = portrait rows shown in each column; hx / ax = portrait columns (crop to the content so it fills the space)
type R = [number, number];
type Lay = { mode: "split"; hl: R; art: R; hx?: R; ax?: R; grid?: boolean } | { mode: "zoom"; win: R; grid?: boolean };
const LAYOUT: Lay[] = [
  { mode: "split", hl: [130, 640], hx: [120, 960], art: [650, 1350], ax: [230, 850] },               // 1 never square
  { mode: "zoom", win: [470, 1260] },                                                                  // 2 cost lives
  { mode: "split", hl: [120, 510], hx: [150, 930], art: [515, 1370] },                                 // 3 1952 comet
  { mode: "split", hl: [170, 960], hx: [90, 990], art: [740, 1440] },                                  // 4 fast high future
  { mode: "zoom", win: [170, 1140] },                                                                  // 5 map
  { mode: "split", hl: [120, 432], art: [445, 1290], ax: [60, 1020], grid: true },                     // 6 tank
  { mode: "split", hl: [140, 450], art: [520, 1310], ax: [110, 990], grid: true },                     // 7 tally
  { mode: "split", hl: [130, 340], art: [335, 1295], ax: [30, 1050] },                                 // 8 crack
  { mode: "split", hl: [120, 440], hx: [100, 980], art: [465, 1385], ax: [90, 990], grid: true },      // 9 puff (starts below the 385 tag)
  { mode: "split", hl: [120, 335], hx: [60, 1020], art: [345, 1265], ax: [60, 1020], grid: true },     // 10 stress
  { mode: "zoom", win: [195, 1325] },                                                                  // 11 metal fatigue sheet
  { mode: "split", hl: [130, 545], hx: [90, 990], art: [575, 1300], ax: [250, 830] },                  // 12 rounded
  { mode: "split", hl: [130, 470], art: [455, 1335], ax: [240, 1000] },                                // 13 lesson
];

type Box = { x: number; y: number; w: number; h: number };
/** shows the portrait canvas region rows src[0]..src[1], columns cols[0]..cols[1], scaled to fit `box`, centred */
const Panel: React.FC<{ box: Box; src: R; cols?: R; clip: boolean; children: React.ReactNode }> = ({ box, src, cols = [0, 1080], clip, children }) => {
  const sh = src[1] - src[0], sw = cols[1] - cols[0];
  const s = Math.min(box.w / sw, box.h / sh);
  const w = sw * s, h = sh * s;
  const ox = box.x + (box.w - w) / 2, oy = box.y + (box.h - h) / 2;
  return (
    <div style={{ position: "absolute", left: ox, top: oy, width: w, height: h, clipPath: clip ? "inset(0px -24px 0px -24px)" : undefined }}>
      <div style={{ position: "absolute", left: -cols[0] * s, top: -src[0] * s, width: 1080, height: 1920, transform: `scale(${s})`, transformOrigin: "0 0" }}>
        {children}
      </div>
    </div>
  );
};

const LEFT: Box = { x: 70, y: 70, w: 840, h: 940 };
const RIGHT: Box = { x: 960, y: 50, w: 900, h: 980 };
const FULL: Box = { x: 0, y: 0, w: 1920, h: 1080 };

export const LAUREN_WIDE: Look = { ...LAUREN, wide: true, dy: 0 };

const WideBody: React.FC<{ look: Look; total: number }> = ({ look, total }) => (
  <LookCtx.Provider value={look}>
    <AbsoluteFill>
      <Defs />
      <PaperBG />
      {SCENES.map(([a, b, Comp], i) => {
        const last = i === SCENES.length - 1;
        const s = Math.max(0, toReal(look, a) - OV), e = last ? total : Math.min(total, toReal(look, b) + OV);
        const lay = LAYOUT[i];
        return (
          <Sequence key={i} from={Math.round(s * FPS)} durationInFrames={Math.round((e - s) * FPS)}>
            <Scene len={e - s} push={last ? 0 : 0.04}>
              {lay.grid && <GridFull />}
              {lay.mode === "split" ? (
                <>
                  <Panel box={LEFT} src={lay.hl} cols={lay.hx} clip><Comp s={s} /></Panel>
                  <Panel box={RIGHT} src={lay.art} cols={lay.ax} clip><Comp s={s} /></Panel>
                </>
              ) : (
                <Panel box={FULL} src={lay.win} clip={false}><Comp s={s} /></Panel>
              )}
            </Scene>
          </Sequence>
        );
      })}
      <PaperOverlay />
    </AbsoluteFill>
  </LookCtx.Provider>
);

export const WindowLaurenWide: React.FC = () => <WideBody look={LAUREN_WIDE} total={DURATION_LAUREN} />;

/* ---------- 16:9 thumbnails (1920 x 1080) ---------- */
const WideText: React.FC<{ l1: string; l2: string; s1?: number; s2?: number }> = ({ l1, l2, s1 = 150, s2 = 200 }) => (
  <div style={{ position: "absolute", left: 90, top: 250, width: 960, fontFamily: OSWALD, fontWeight: 700, textTransform: "uppercase", lineHeight: 1.0, color: C.ink }}>
    <div style={{ fontSize: s1 }}>{l1}</div>
    <div style={{ fontSize: s2, transform: "rotate(-2deg)", transformOrigin: "left center", whiteSpace: "nowrap" }}><Hi p={1}>{l2}</Hi></div>
  </div>
);

export const WideThumbA: React.FC = () => (
  <LookCtx.Provider value={LAUREN_WIDE}>
    <AbsoluteFill>
      <Defs /><PaperBG />
      <WideText l1="This shape" l2="was deadly" s2={190} />
      <div style={{ position: "absolute", left: 1090, top: 170, width: 470, height: 650, transform: "rotate(-4deg)" }}>
        <CutOut tape style={{ width: "100%", height: "100%" }}><WindowArt square drift={60} /></CutOut>
      </div>
      <div style={{ position: "absolute", left: 1600, top: 560, width: 230, height: 322, transform: "rotate(5deg)" }}>
        <CutOut style={{ width: "100%", height: "100%" }}><WindowArt drift={160} /></CutOut>
      </div>
      <svg viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, overflow: "visible" }}>
        <Draw d={loopPath(1500, 240, 125, 110)} p={1} w={15} />
        <Arrow a={[1830, 150]} b={[1640, 230]} bend={-50} p={1} w={15} />
        <path d="M 1650 500 L 1695 538 L 1790 448" fill="none" stroke={C.green} strokeWidth={20} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <PaperOverlay />
    </AbsoluteFill>
  </LookCtx.Provider>
);

export const WideThumbB: React.FC = () => (
  <LookCtx.Provider value={LAUREN_WIDE}>
    <AbsoluteFill>
      <Defs /><PaperBG />
      <WideText l1="Why not" l2="square?" s1={160} s2={230} />
      <div style={{ position: "absolute", left: 110, top: 760, transform: "rotate(-5deg)", background: C.ink, color: C.yellow, fontFamily: OSWALD, fontWeight: 700, fontSize: 96, padding: "6px 34px", filter: "url(#shadow)" }}>1954</div>
      <div style={{ position: "absolute", left: 960, top: 480, transform: "rotate(-6deg)" }}>
        <CutOut tape><CometArt width={1000} uid="wtb" /></CutOut>
      </div>
      <svg viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, overflow: "visible" }}>
        <Draw d={loopPath(1385, 612, 135, 88)} p={1} w={15} />
        <Arrow a={[1640, 940]} b={[1440, 700]} bend={70} p={1} w={15} />
      </svg>
      <PaperOverlay />
    </AbsoluteFill>
  </LookCtx.Provider>
);
