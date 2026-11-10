import React, { createContext, useContext } from "react";
import { AbsoluteFill, Easing, Img, interpolate, random, spring, staticFile, useCurrentFrame } from "remotion";
import { continueRender, delayRender } from "remotion";

// Fonts are bundled in public/fonts (SIL OFL, from Fontsource) so renders need no network (the daily cloud
// session cannot reach Google Fonts). latin covers en/de/fr/es/pt; latin-ext the rest of Europe.
const LATIN = "U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD";
const LATIN_EXT = "U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF";
const loadLocal = (family: string, file: string, weights: string[], style = "normal") => {
  if (typeof document === "undefined") return family;
  const h = delayRender("font " + family);
  const faces = weights.flatMap((w) => [["latin", LATIN], ["latin-ext", LATIN_EXT]].map(([sub, range]) =>
    new FontFace(family, `url(${staticFile(`fonts/${file}-${sub}-${w}-${style}.woff2`)}) format("woff2")`,
      { weight: w, style, unicodeRange: range })));
  Promise.all(faces.map((f) => f.load().then((x) => { document.fonts.add(x); })))
    .then(() => continueRender(h)).catch((e) => { console.error(e); continueRender(h); });
  return family;
};

export const FPS = 30;
export const OSWALD = loadLocal("Oswald", "oswald", ["500", "700"]);
export const SERIF = loadLocal("Libre Baskerville", "libre-baskerville", ["400", "700"]);
export const SERIF_I = loadLocal("Libre Baskerville Italic", "libre-baskerville", ["400"], "italic");

export const C = {
  ink: "#171513", paper: "#F2ECE0", yellow: "#FFD400", red: "#E63946", green: "#2E9E5B",
  sea: "#B7CFD8", land: "#EFE7D5", italy: "#E6D09C", silver: "#C3C8CD", steel: "#8E979F",
  dark: "#1D1B19", blue: "#2F5D7C", glass: "#1F2A33",
};

/* ---------- look: narrator time map + texture level ----------
   Scenes are timed on the base (Andrew) timeline. `real`/`base` map the actual narrator's time onto it,
   so the same scenes follow any read of the same script. rich = heavier Vox texture pack. dy = layout shift. */
export type Look = { real: number[]; base: number[]; rich: boolean; dy: number; wide?: boolean };
export const BASE_LOOK: Look = { real: [], base: [], rich: false, dy: 0 };
export const LookCtx = createContext<Look>(BASE_LOOK);
export const useLook = () => useContext(LookCtx);
const lerpMap = (x: number, xs: number[], ys: number[]) => {
  if (!xs.length) return x;
  if (x <= xs[0]) return ys[0] + (x - xs[0]);
  if (x >= xs[xs.length - 1]) return ys[ys.length - 1] + (x - xs[xs.length - 1]);
  let lo = 0, hi = xs.length - 1;
  while (hi - lo > 1) { const m = (lo + hi) >> 1; if (xs[m] <= x) lo = m; else hi = m; }
  return ys[lo] + ((x - xs[lo]) / (xs[hi] - xs[lo])) * (ys[hi] - ys[lo]);
};
export const toBase = (L: Look, real: number) => lerpMap(real, L.real, L.base);
export const toReal = (L: Look, base: number) => lerpMap(base, L.base, L.real);

/** base-timeline time (s) inside a Sequence that starts at real second `s` */
export const useT = (s: number) => {
  const f = useCurrentFrame();
  return toBase(useLook(), f / FPS + s);
};
export const ramp = (t: number, a: number, b: number, ease: (n: number) => number = Easing.inOut(Easing.cubic)) =>
  interpolate(t, [a, b], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease });
export const pop = (t: number, a: number, damping = 11, stiffness = 170) =>
  t < a ? 0 : spring({ frame: (t - a) * FPS, fps: FPS, config: { damping, stiffness, mass: 0.8 } });

/** paper background that drifts very slowly so the frame is never dead still */
const paperFile = (L: Look) => (L.wide ? "paper2w.png" : L.rich ? "paper2.png" : "paper.png");
export const PaperBG: React.FC = () => {
  const f = useCurrentFrame();
  const L = useLook();
  return (
    <AbsoluteFill style={{ background: C.paper, overflow: "hidden" }}>
      <Img src={staticFile(paperFile(L))} style={{ width: "100%", height: "100%", transform: `scale(1.06) translate(${Math.sin(f / 70) * 8}px, ${Math.cos(f / 85) * 8}px)` }} />
    </AbsoluteFill>
  );
};

/** paper multiplied over everything; rich adds film grain, dust, hairline scratches, flicker and vignette */
export const PaperOverlay: React.FC = () => {
  const f = useCurrentFrame();
  const L = useLook();
  const { rich } = L;
  const VW = L.wide ? 1920 : 1080, VH = L.wide ? 1080 : 1920;
  const k = Math.floor(f / 2);
  const dx = (random(`x${k}`) - 0.5) * 8, dy = (random(`y${k}`) - 0.5) * 8;
  const specks = rich ? Array.from({ length: 7 }).map((_, i) => ({
    x: random(`sx${k}-${i}`) * VW, y: random(`sy${k}-${i}`) * VH, r: 1.2 + random(`sr${k}-${i}`) * 3.2, o: 0.2 + random(`so${k}-${i}`) * 0.35,
  })) : [];
  const scratch = rich && random(`sc${k}`) < 0.3;
  const hair = rich && random(`hr${Math.floor(f / 5)}`) < 0.12;
  return (
    <>
      <AbsoluteFill style={{ mixBlendMode: "multiply", opacity: rich ? 0.62 : 0.6, pointerEvents: "none", overflow: "hidden" }}>
        <Img src={staticFile(paperFile(L))} style={{ width: "100%", height: "100%", transform: `scale(1.03) translate(${dx}px, ${dy}px)` }} />
      </AbsoluteFill>
      {rich && (
        <>
          <AbsoluteFill style={{ mixBlendMode: "overlay", opacity: 0.32, pointerEvents: "none", overflow: "hidden" }}>
            <Img src={staticFile(`grain${f % 6}.png`)} style={{ width: "100%", height: "100%", imageRendering: "auto" }} />
          </AbsoluteFill>
          <svg viewBox={`0 0 ${VW} ${VH}`} style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}>
            {specks.map((s, i) => <circle key={i} cx={s.x} cy={s.y} r={s.r} fill="#2A2420" opacity={s.o} />)}
            {scratch && (() => {
              const x = random(`scx${k}`) * VW, y = random(`scy${k}`) * (VH * 0.62);
              return <line x1={x} y1={y} x2={x + (random(`scw${k}`) - 0.5) * 20} y2={y + 300 + random(`scl${k}`) * 600} stroke={random(`scc${k}`) < 0.5 ? "#2A2420" : "#FFFFFF"} strokeWidth={1.4} opacity={0.3} />;
            })()}
            {hair && (() => {
              const h = Math.floor(f / 5), x = random(`hx${h}`) * (VW - 80), y = random(`hy${h}`) * (VH - 120);
              return <path d={`M ${x} ${y} q 30 -40 70 -10 t 60 30`} fill="none" stroke="#2A2420" strokeWidth={1.6} opacity={0.35} />;
            })()}
          </svg>
          <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, rgba(0,0,0,0) 62%, rgba(40,25,10,0.12) 100%)", pointerEvents: "none" }} />
          <AbsoluteFill style={{ background: "#000", opacity: 0.012 + 0.025 * random(`fl${k}`), pointerEvents: "none" }} />
        </>
      )}
    </>
  );
};

const DOT = encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="7" height="7"><circle cx="3.5" cy="3.5" r="1.25" fill="#000" fill-opacity="0.16"/></svg>`);

/** SVG filters: #cut = white cut-out border + shadow; #cutx = printed cut-out (paper tooth + halftone) + border + shadow;
    #tex = printed texture only (for maps); #shadow = shadow only */
export const Defs: React.FC = () => (
  <svg width={0} height={0} style={{ position: "absolute" }}>
    <defs>
      <filter id="cut" x="-20%" y="-20%" width="140%" height="150%" colorInterpolationFilters="sRGB">
        <feMorphology in="SourceAlpha" operator="dilate" radius="8" result="d" />
        <feFlood floodColor="#FFFFFF" result="w" />
        <feComposite in="w" in2="d" operator="in" result="border" />
        <feGaussianBlur in="d" stdDeviation="9" result="b" />
        <feOffset in="b" dx="8" dy="14" result="o" />
        <feFlood floodColor="#000000" floodOpacity="0.33" />
        <feComposite in2="o" operator="in" result="shadow" />
        <feMerge><feMergeNode in="shadow" /><feMergeNode in="border" /><feMergeNode in="SourceGraphic" /></feMerge>
      </filter>
      <filter id="cutx" x="-20%" y="-20%" width="140%" height="150%" colorInterpolationFilters="sRGB">
        <feMorphology in="SourceAlpha" operator="dilate" radius="9" result="d" />
        <feFlood floodColor="#FBF7EC" result="w" />
        <feComposite in="w" in2="d" operator="in" result="border" />
        <feImage href={`data:image/svg+xml,${DOT}`} x="0" y="0" width="7" height="7" result="dot" />
        <feTile in="dot" result="dots" />
        <feComposite in="dots" in2="SourceAlpha" operator="in" result="dotsIn" />
        <feMerge result="card"><feMergeNode in="border" /><feMergeNode in="SourceGraphic" /><feMergeNode in="dotsIn" /></feMerge>
        <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="2" seed="7" result="n" />
        <feColorMatrix in="n" type="matrix" values="0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0 0 0 0 1" result="ng" />
        <feComponentTransfer in="ng" result="tooth">
          <feFuncR type="linear" slope="0.35" intercept="0.74" /><feFuncG type="linear" slope="0.35" intercept="0.73" /><feFuncB type="linear" slope="0.35" intercept="0.70" />
        </feComponentTransfer>
        <feBlend in="card" in2="tooth" mode="multiply" result="printed" />
        <feComposite in="printed" in2="d" operator="in" result="clipped" />
        <feGaussianBlur in="d" stdDeviation="10" result="b" />
        <feOffset in="b" dx="9" dy="16" result="o" />
        <feFlood floodColor="#2A1A08" floodOpacity="0.36" />
        <feComposite in2="o" operator="in" result="shadow" />
        <feMerge><feMergeNode in="shadow" /><feMergeNode in="clipped" /></feMerge>
      </filter>
      <filter id="tex" x="0" y="0" width="100%" height="100%" colorInterpolationFilters="sRGB">
        <feImage href={`data:image/svg+xml,${DOT}`} x="0" y="0" width="7" height="7" result="dot" />
        <feTile in="dot" result="dots" />
        <feComposite in="dots" in2="SourceAlpha" operator="in" result="dotsIn" />
        <feMerge result="card"><feMergeNode in="SourceGraphic" /><feMergeNode in="dotsIn" /></feMerge>
        <feTurbulence type="fractalNoise" baseFrequency="0.7" numOctaves="2" seed="3" result="n" />
        <feColorMatrix in="n" type="matrix" values="0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0.33 0.33 0.33 0 0  0 0 0 0 1" result="ng" />
        <feComponentTransfer in="ng" result="tooth">
          <feFuncR type="linear" slope="0.3" intercept="0.78" /><feFuncG type="linear" slope="0.3" intercept="0.77" /><feFuncB type="linear" slope="0.3" intercept="0.74" />
        </feComponentTransfer>
        <feBlend in="card" in2="tooth" mode="multiply" result="printed" />
        <feComposite in="printed" in2="SourceAlpha" operator="in" />
      </filter>
      <filter id="shadow" x="-20%" y="-20%" width="140%" height="150%" colorInterpolationFilters="sRGB">
        <feGaussianBlur in="SourceAlpha" stdDeviation="8" result="b" />
        <feOffset in="b" dx="6" dy="12" result="o" />
        <feFlood floodColor="#000000" floodOpacity="0.3" />
        <feComposite in2="o" operator="in" result="shadow" />
        <feMerge><feMergeNode in="shadow" /><feMergeNode in="SourceGraphic" /></feMerge>
      </filter>
    </defs>
  </svg>
);

/** strip of masking tape */
export const Tape: React.FC<{ x: number | string; y: number | string; rot: number; w?: number }> = ({ x, y, rot, w = 170 }) => {
  const zig = "polygon(0% 8%, 3% 0%, 6% 10%, 9% 2%, 91% 0%, 94% 9%, 97% 1%, 100% 10%, 100% 92%, 97% 100%, 94% 90%, 91% 99%, 9% 100%, 6% 91%, 3% 100%, 0% 92%)";
  return (
    <div style={{ position: "absolute", left: x, top: y, width: w, height: 50, transform: `translate(-50%, -50%) rotate(${rot}deg)`, filter: "drop-shadow(1px 2px 1.5px rgba(0,0,0,0.25))", pointerEvents: "none" }}>
      <div style={{ width: "100%", height: "100%", clipPath: zig, background: "linear-gradient(180deg, rgba(240,229,196,0.88), rgba(226,212,170,0.86))" }} />
    </div>
  );
};

export const CutOut: React.FC<{ children: React.ReactNode; style?: React.CSSProperties; tape?: boolean }> = ({ children, style, tape }) => {
  const { rich } = useLook();
  return (
    <div style={{ position: "relative", ...style }}>
      <div style={{ filter: rich ? "url(#cutx)" : "url(#cut)", width: "100%", height: "100%" }}>{children}</div>
      {rich && tape && (<><Tape x="10%" y="2%" rot={-38} /><Tape x="90%" y="3%" rot={36} /></>)}
    </div>
  );
};

/** engineering graph paper (rich look only) */
export const Grid: React.FC = () => {
  const { rich, wide } = useLook();
  if (!rich || wide) return null;   // the wide layout draws one full-frame sheet instead (GridFull)
  return (
    <svg viewBox="0 0 1080 1920" style={{ position: "absolute", left: -60, top: -120, width: 1200, height: 2160, opacity: 0.55 }}>
      <defs>
        <pattern id="gmin" width={36} height={36} patternUnits="userSpaceOnUse"><path d="M 36 0 L 0 0 0 36" fill="none" stroke="#7FA6C6" strokeWidth={1} /></pattern>
        <pattern id="gmaj" width={180} height={180} patternUnits="userSpaceOnUse"><rect width={180} height={180} fill="url(#gmin)" /><path d="M 180 0 L 0 0 0 180" fill="none" stroke="#5E8DB3" strokeWidth={2.2} /></pattern>
      </defs>
      <rect width={1080} height={1920} fill="url(#gmaj)" />
    </svg>
  );
};

/** full-frame graph paper for the wide (16:9) layout */
export const GridFull: React.FC = () => (
  <svg viewBox="0 0 1920 1080" style={{ position: "absolute", left: -40, top: -40, width: 2000, height: 1160, opacity: 0.55 }}>
    <defs>
      <pattern id="wgmin" width={36} height={36} patternUnits="userSpaceOnUse"><path d="M 36 0 L 0 0 0 36" fill="none" stroke="#7FA6C6" strokeWidth={1} /></pattern>
      <pattern id="wgmaj" width={180} height={180} patternUnits="userSpaceOnUse"><rect width={180} height={180} fill="url(#wgmin)" /><path d="M 180 0 L 0 0 0 180" fill="none" stroke="#5E8DB3" strokeWidth={2.2} /></pattern>
    </defs>
    <rect width={1920} height={1080} fill="url(#wgmaj)" />
  </svg>
);

/** yellow highlighter swipe behind text, p = 0..1 */
export const Hi: React.FC<{ p: number; children: React.ReactNode; color?: string }> = ({ p, children, color = C.yellow }) => (
  <span style={{ position: "relative", display: "inline-block", padding: "0 0.1em" }}>
    <span style={{ position: "absolute", left: 0, right: 0, top: "22%", bottom: "6%", background: color, transform: `scaleX(${p}) rotate(-1.2deg)`, transformOrigin: "left center", borderRadius: "0.08em 0.2em 0.1em 0.25em", opacity: 0.95 }} />
    <span style={{ position: "relative" }}>{children}</span>
  </span>
);

/** big condensed headline word that slams in at `at` */
export const Slam: React.FC<{ t: number; at: number; children: React.ReactNode; size?: number; color?: string; out?: number; style?: React.CSSProperties }> = ({ t, at, children, size = 160, color = C.ink, out, style }) => {
  const p = pop(t, at, 12, 230);
  const o = ramp(t, at, at + 0.06, Easing.linear) * (out ? 1 - ramp(t, out, out + 0.15) : 1);
  return (
    <div style={{ fontFamily: OSWALD, fontWeight: 700, fontSize: size, lineHeight: 1.02, color, textTransform: "uppercase", letterSpacing: "0.005em", transform: `scale(${1.45 - 0.45 * p})`, opacity: o, ...style }}>
      {children}
    </div>
  );
};

/** paper label tag that pops in */
export const Tag: React.FC<{ t: number; at: number; x: number; y: number; children: React.ReactNode; rot?: number; bg?: string; color?: string; size?: number; font?: string; out?: number }> = ({ t, at, x, y, children, rot = -2, bg = "#FFFFFF", color = C.ink, size = 54, font, out }) => {
  const p = pop(t, at, 13, 200);
  const o = (t >= at ? 1 : 0) * (out ? 1 - ramp(t, out, out + 0.15) : 1);
  return (
    <div style={{ position: "absolute", left: x, top: y, transform: `translate(-50%, -50%) scale(${p}) rotate(${rot}deg)`, opacity: o, filter: "url(#shadow)" }}>
      <div style={{ background: bg, color, fontFamily: font ?? OSWALD, fontWeight: font ? 400 : 700, fontSize: size, padding: "0.16em 0.45em", whiteSpace: "nowrap", letterSpacing: font ? 0 : "0.03em", textTransform: font ? "none" : "uppercase" }}>
        {children}
      </div>
    </div>
  );
};

/** path that draws itself, p = 0..1 */
export const Draw: React.FC<{ d: string; p: number; stroke?: string; w?: number; opacity?: number }> = ({ d, p, stroke = C.red, w = 10, opacity = 1 }) => (
  <path d={d} pathLength={1} fill="none" stroke={stroke} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round"
    strokeDasharray="1 1" strokeDashoffset={1 - p} opacity={p > 0.001 ? opacity : 0} />
);

/** hand-drawn loop (marker circle that overshoots) */
export const loopPath = (cx: number, cy: number, rx: number, ry: number) => {
  const n = 80, pts: string[] = [];
  for (let i = 0; i <= n; i++) {
    const u = i / n, th = -2.3 + u * (Math.PI * 2 + 0.7), k = 1 + 0.045 * Math.sin(th * 3 + 1) + 0.07 * u;
    pts.push(`${(cx + rx * k * Math.cos(th)).toFixed(1)} ${(cy + ry * k * Math.sin(th)).toFixed(1)}`);
  }
  return "M" + pts.join(" L");
};

/** arrow (curved shaft + head) from a to b */
export const Arrow: React.FC<{ a: [number, number]; b: [number, number]; bend?: number; p: number; stroke?: string; w?: number }> = ({ a, b, bend = 80, p, stroke = C.red, w = 12 }) => {
  const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy);
  const cx = mx - (dy / L) * bend, cy = my + (dx / L) * bend;
  const ang = Math.atan2(b[1] - cy, b[0] - cx), h = 46;
  const head = `M ${b[0] - h * Math.cos(ang - 0.45)} ${b[1] - h * Math.sin(ang - 0.45)} L ${b[0]} ${b[1]} L ${b[0] - h * Math.cos(ang + 0.45)} ${b[1] - h * Math.sin(ang + 0.45)}`;
  return (
    <g>
      <Draw d={`M ${a[0]} ${a[1]} Q ${cx} ${cy} ${b[0]} ${b[1]}`} p={Math.min(1, p * 1.25)} stroke={stroke} w={w} />
      <Draw d={head} p={Math.max(0, (p - 0.8) * 5)} stroke={stroke} w={w} />
    </g>
  );
};

/** scene wrapper: slides in from the right, slow camera push, slides out to the left */
export const Scene: React.FC<{ len: number; children: React.ReactNode; push?: number }> = ({ len, children, push = 0.05 }) => {
  const f = useCurrentFrame();
  const { dy } = useLook();
  const total = len * FPS;
  const inP = interpolate(f, [0, 8], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const outP = interpolate(f, [total - 7, total], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic) });
  const s = 1 + push * (f / total);
  return (
    <AbsoluteFill style={{ transform: `translateX(${(1 - inP) * 120 - outP * 140}px) translateY(${dy}px) scale(${s})`, opacity: inP * (1 - outP) }}>
      {children}
    </AbsoluteFill>
  );
};
