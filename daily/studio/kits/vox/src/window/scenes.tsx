import React from "react";
import { AbsoluteFill, Easing, interpolate, random } from "remotion";
import { Arrow, C, CutOut, Draw, Grid, Hi, OSWALD, SERIF, SERIF_I, Slam, Tag, Tape, loopPath, pop, ramp, useLook, useT } from "./ui";
import { CometArt, CometG, PLANE, WindowArt } from "./art";
import { LAND, P } from "./map";

type SP = { s: number };
const full: React.CSSProperties = { position: "absolute", inset: 0, width: "100%", height: "100%", overflow: "visible" };
const top = (y: number): React.CSSProperties => ({ position: "absolute", top: y, left: 0, right: 0, textAlign: "center" });

/* 1  0.0–3.0  "You will never see a square window on a passenger jet." */
export const S1: React.FC<SP> = ({ s }) => {
  const t = useT(s);
  const w = pop(t, 0.12, 13, 120);
  return (
    <AbsoluteFill>
      <div style={top(170)}>
        <Slam t={t} at={0.32} size={170}>Never</Slam>
        <Slam t={t} at={0.86} size={240}><Hi p={ramp(t, 1.0, 1.35)}>Square</Hi></Slam>
      </div>
      <div style={{ position: "absolute", left: 300, top: 690, width: 480, height: 620, transform: `scale(${w}) rotate(-3deg)` }}>
        <CutOut tape style={{ width: "100%", height: "100%" }}><WindowArt square drift={t * 40} /></CutOut>
      </div>
      <svg viewBox="0 0 1080 1920" style={full}>
        <Draw d="M 290 720 L 800 1290" p={ramp(t, 1.3, 1.55)} w={30} />
        <Draw d="M 800 720 L 290 1290" p={ramp(t, 1.55, 1.8)} w={30} />
      </svg>
    </AbsoluteFill>
  );
};

/* 2  3.0–4.9  "And the reason cost lives." */
export const S2: React.FC<SP> = ({ s }) => {
  const t = useT(s);
  const p = pop(t, 3.05, 14, 160);
  const torn = "M 0 40 L 60 18 L 140 46 L 230 12 L 330 38 L 420 8 L 540 34 L 640 6 L 760 30 L 860 10 L 980 36 L 1080 14 L 1080 560 L 990 590 L 880 566 L 770 596 L 650 570 L 540 600 L 420 572 L 300 598 L 190 570 L 80 594 L 0 572 Z";
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: -40, top: 560, width: 1160, height: 620, transform: `rotate(-3deg) scaleY(${p})`, filter: "url(#shadow)" }}>
        <svg viewBox="0 0 1080 610" width="100%" height="100%" preserveAspectRatio="none"><path d={torn} fill={C.dark} /></svg>
      </div>
      <div style={{ ...top(690), transform: "rotate(-3deg)" }}>
        <Slam t={t} at={3.25} size={130} color="#F2ECE0">The reason</Slam>
        <Slam t={t} at={3.68} size={190} color={C.red}>Cost lives</Slam>
      </div>
      <svg viewBox="0 0 1080 1920" style={full}>
        <Draw d="M 170 1105 C 400 1088, 700 1080, 930 1070" p={ramp(t, 4.1, 4.45)} stroke={C.yellow} w={14} />
      </svg>
    </AbsoluteFill>
  );
};

/* 3  4.9–11.0  "1952. Britain launches the de Havilland Comet, the world's first jet airliner." */
export const S3: React.FC<SP> = ({ s }) => {
  const t = useT(s);
  const slide = ramp(t, 6.35, 7.25, Easing.out(Easing.cubic));
  const x = interpolate(slide, [0, 1], [1250, 40]);
  const bob = Math.sin(t * 2.2) * 6;
  return (
    <AbsoluteFill>
      <div style={{ ...top(150), transform: `rotate(-4deg) scale(${1.6 - 0.6 * pop(t, 4.95, 10, 200)})`, opacity: t > 4.95 ? 1 : 0 }}>
        <div style={{ fontFamily: OSWALD, fontWeight: 700, fontSize: 330, color: C.ink, lineHeight: 1 }}>1952</div>
      </div>
      <Tag t={t} at={6.42} x={400} y={565} rot={-4} bg={C.blue} color="#FFFFFF" size={56}>Britain</Tag>
      <div style={{ position: "absolute", left: x, top: 660 + bob, transform: "rotate(-2deg)" }}>
        <CutOut tape><CometArt width={1000} uid="s3" /></CutOut>
      </div>
      <Tag t={t} at={7.35} x={560} y={1010} rot={1.5} font={SERIF} size={50}>de Havilland Comet</Tag>
      <div style={top(1105)}>
        <Slam t={t} at={8.85} size={112}>World&apos;s first <Hi p={ramp(t, 9.25, 9.7)}>jet airliner</Hi></Slam>
      </div>
    </AbsoluteFill>
  );
};

/* 4  11.0–13.4  "Fast. High. The future." */
export const S4: React.FC<SP> = ({ s }) => {
  const t = useT(s);
  const fly = ramp(t, 10.9, 13.5, Easing.linear);
  const x = interpolate(fly, [0, 1], [-700, 700]), y = interpolate(fly, [0, 1], [1230, 820]);
  return (
    <AbsoluteFill>
      <svg viewBox="0 0 1080 1920" style={full}>
        {[0, 1, 2, 3, 4].map((i) => (
          <line key={i} x1={x - 40 - i * 30} y1={y + 70 + i * 26} x2={x - 460 - i * 60} y2={y + 160 + i * 40} stroke={C.ink} strokeWidth={5} opacity={0.25} strokeLinecap="round" />
        ))}
      </svg>
      <div style={{ position: "absolute", left: x, top: y, transform: "rotate(-14deg)" }}>
        {/* the artwork faces left; mirror it so the nose leads while it flies left -> right */}
        <CutOut><div style={{ transform: "scaleX(-1)" }}><CometArt width={720} uid="s4" /></div></CutOut>
      </div>
      <div style={top(200)}><Slam t={t} at={11.05} size={250}>Fast.</Slam></div>
      <div style={top(470)}><Slam t={t} at={11.88} size={250}>High.</Slam></div>
      <div style={top(740)}><Slam t={t} at={12.55} size={165} color={C.red}>The future.</Slam></div>
    </AbsoluteFill>
  );
};

/* 5  13.4–22.4  map: Rome -> Elba (Jan 1954), Rome -> Naples (Apr 1954) */
const ROME = P(12.59, 41.8), ELBA = P(10.45, 42.68), NAPLES = P(14.0, 40.62);
const Crash: React.FC<{ t: number; at: number; at2: number; pt: [number, number]; label: string; lx: number; ly: number }> = ({ t, at, at2, pt, label, lx, ly }) => {
  if (t < at) return null;
  const ph = ((t - at) % 1.1) / 1.1;
  const k = pop(t, at, 9, 220);
  return (
    <g>
      <circle cx={pt[0]} cy={pt[1]} r={24 + 80 * ph} fill="none" stroke={C.red} strokeWidth={6} opacity={1 - ph} />
      <g transform={`translate(${pt[0]} ${pt[1]}) scale(${k})`}>
        <path d="M -26 -26 L 26 26 M 26 -26 L -26 26" stroke={C.red} strokeWidth={14} strokeLinecap="round" />
      </g>
      <g opacity={t > at2 ? 1 : 0} transform={`translate(${lx} ${ly}) scale(${pop(t, at2, 13, 200)}) rotate(-2)`}>
        <rect x={-150} y={-40} width={300} height={80} fill="#FFFFFF" filter="url(#shadow)" />
        <text x={0} y={18} textAnchor="middle" fontFamily={OSWALD} fontWeight={700} fontSize={50} fill={C.ink}>{label}</text>
      </g>
    </g>
  );
};
const Flight: React.FC<{ t: number; a: number; b: number; to: [number, number] }> = ({ t, a, b, to }) => {
  if (t < a) return null;
  const p = ramp(t, a, b, Easing.inOut(Easing.quad));
  const x = ROME[0] + (to[0] - ROME[0]) * p, y = ROME[1] + (to[1] - ROME[1]) * p;
  const ang = (Math.atan2(to[1] - ROME[1], to[0] - ROME[0]) * 180) / Math.PI;
  return (
    <g>
      <line x1={ROME[0]} y1={ROME[1]} x2={x} y2={y} stroke={C.ink} strokeWidth={6} strokeDasharray="4 16" strokeLinecap="round" />
      {t < b && <path d={PLANE} transform={`translate(${x} ${y}) rotate(${ang}) scale(1.3)`} fill={C.ink} stroke="#FFFFFF" strokeWidth={3} />}
    </g>
  );
};
export const SMap: React.FC<SP> = ({ s }) => {
  const t = useT(s);
  const z = interpolate(ramp(t, 13.45, 15.1), [0, 1], [0.3, 1]);
  const lab = ramp(t, 15.0, 15.4);
  const IT = P(13.4, 42.75), TS = P(11.3, 40.55);
  const { rich } = useLook();
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: -600, right: -600, top: -300, bottom: -300, background: C.sea }} />
      <svg viewBox="0 0 1080 1920" style={full}>
        <g transform={`translate(540 760) scale(${z}) translate(-540 -760)`} filter={rich ? "url(#tex)" : undefined}>
          {LAND.map((l, i) => (
            <path key={i} d={l.d} fill={l.italy ? C.italy : C.land} stroke={C.ink} strokeWidth={2.4} vectorEffect="non-scaling-stroke" strokeLinejoin="round" />
          ))}
        </g>
        <g opacity={lab}>
          <text x={IT[0]} y={IT[1]} textAnchor="middle" fontFamily={OSWALD} fontWeight={700} fontSize={78} letterSpacing={18} fill={C.ink} opacity={0.35} transform={`rotate(32 ${IT[0]} ${IT[1]})`}>ITALY</text>
          <text x={TS[0]} y={TS[1]} textAnchor="middle" fontFamily={SERIF_I} fontSize={40} fill={C.blue} opacity={0.75}>Tyrrhenian Sea</text>
          <circle cx={ROME[0]} cy={ROME[1]} r={13} fill={C.ink} />
          <text x={ROME[0] + 24} y={ROME[1] + 14} fontFamily={OSWALD} fontWeight={700} fontSize={44} fill={C.ink}>ROME</text>
        </g>
        <Flight t={t} a={15.65} b={16.95} to={ELBA} />
        <Crash t={t} at={16.95} at2={17.95} pt={ELBA} label="NEAR ELBA" lx={ELBA[0] + 30} ly={ELBA[1] - 120} />
        <Flight t={t} a={20.7} b={21.5} to={NAPLES} />
        <Crash t={t} at={21.5} at2={21.6} pt={NAPLES} label="NEAR NAPLES" lx={NAPLES[0] - 10} ly={NAPLES[1] + 120} />
      </svg>
      <Tag t={t} at={13.6} x={540} y={250} rot={-2} bg={C.yellow} size={88} out={19.45}>January 1954</Tag>
      <Tag t={t} at={19.6} x={540} y={250} rot={2} bg={C.yellow} size={88}>April 1954</Tag>
    </AbsoluteFill>
  );
};

/* 6  22.4–28.6  the water tank test */
export const STank: React.FC<SP> = ({ s }) => {
  const t = useT(s);
  const tank = pop(t, 22.45, 14, 120);
  const sink = ramp(t, 23.5, 24.6, Easing.out(Easing.cubic));
  const fy = interpolate(sink, [0, 1], [300, 760]);
  const water = ramp(t, 24.3, 25.9);
  const wTop = interpolate(water, [0, 1], [1230, 640]);
  const cyc = t > 26.45 && t < 28.65 ? Math.max(0, Math.sin(((t - 26.45) * Math.PI * 2) / 0.69)) : 0;
  const wave = (y: number) => {
    let d = `M 110 ${y}`;
    for (let x = 110; x <= 970; x += 20) d += ` L ${x} ${y + Math.sin(x / 45 + t * 4) * 7}`;
    return d + " L 970 1240 L 110 1240 Z";
  };
  const needle = -120 + 220 * cyc;
  return (
    <AbsoluteFill>
      <Grid />
      <div style={top(150)}><Slam t={t} at={22.55} size={150}>The tank test</Slam></div>
      <Tag t={t} at={23.1} x={540} y={385} rot={-1} font={SERIF} size={40}>Farnborough, England, 1954</Tag>
      <svg viewBox="0 0 1080 1920" style={full}>
        <g transform={`translate(540 1240) scale(${tank}) translate(-540 -1240)`}>
          {[140, 540, 940].map((x) => <line key={x} x1={x} y1={470} x2={x} y2={1260} stroke="#6B6259" strokeWidth={10} />)}
          <line x1={90} y1={500} x2={990} y2={500} stroke="#6B6259" strokeWidth={10} />
          <rect x={100} y={520} width={880} height={730} fill="#FFFFFF" opacity={0.35} stroke={C.ink} strokeWidth={10} filter="url(#shadow)" />
          <g transform={`translate(540 ${fy + 34}) scale(0.84 ${0.84 * (1 + 0.06 * cyc)}) translate(-500 -130)`}>
            <CometG wing={false} uid="tank" />
          </g>
          {water > 0 && <path d={wave(wTop)} fill="#3F86B5" opacity={0.5} />}
          {water > 0.6 && Array.from({ length: 16 }).map((_, i) => {
            const bx = 140 + random(`bx${i}`) * 800, sp = 90 + random(`bs${i}`) * 90;
            const by = 1230 - (((t * sp) + random(`by${i}`) * 600) % (1230 - wTop - 20));
            return <circle key={i} cx={bx + Math.sin(t * 3 + i) * 8} cy={by} r={5 + random(`br${i}`) * 7} fill="none" stroke="#FFFFFF" strokeWidth={3} opacity={0.8} />;
          })}
          <rect x={100} y={520} width={880} height={730} fill="none" stroke={C.ink} strokeWidth={10} />
        </g>
        <g opacity={ramp(t, 26.3, 26.5)} transform="translate(880 560)">
          <circle r={86} fill="#FFFFFF" stroke={C.ink} strokeWidth={8} filter="url(#shadow)" />
          {Array.from({ length: 9 }).map((_, i) => {
            const a = ((-120 + i * 27.5) * Math.PI) / 180;
            return <line key={i} x1={Math.sin(a) * 58} y1={-Math.cos(a) * 58} x2={Math.sin(a) * 72} y2={-Math.cos(a) * 72} stroke={i > 6 ? C.red : C.ink} strokeWidth={6} />;
          })}
          <line x1={0} y1={0} x2={Math.sin((needle * Math.PI) / 180) * 62} y2={-Math.cos((needle * Math.PI) / 180) * 62} stroke={C.red} strokeWidth={9} strokeLinecap="round" />
          <circle r={11} fill={C.ink} />
          <text y={50} textAnchor="middle" fontFamily={OSWALD} fontWeight={700} fontSize={22} fill={C.ink}>PRESSURE</text>
        </g>
      </svg>
    </AbsoluteFill>
  );
};

/* 7  28.6–30.4  "Thousands of fake flights." tally marks fill the page */
export const STally: React.FC<SP> = ({ s }) => {
  const t = useT(s);
  const COLS = 6, ROWS = 6, total = COLS * ROWS * 5;
  const n = Math.floor(ramp(t, 28.7, 30.2, Easing.in(Easing.quad)) * total);
  const marks: React.ReactNode[] = [];
  for (let k = 0; k < n; k++) {
    const g = Math.floor(k / 5), m = k % 5, col = g % COLS, row = Math.floor(g / COLS);
    const gx = 150 + col * 140, gy = 560 + row * 120;
    const j = (q: string) => (random(`${q}${k}`) - 0.5) * 8;
    marks.push(m < 4
      ? <line key={k} x1={gx + m * 22 + j("a")} y1={gy + j("b")} x2={gx + m * 22 + j("c")} y2={gy + 92 + j("d")} stroke={C.ink} strokeWidth={8} strokeLinecap="round" />
      : <line key={k} x1={gx - 14} y1={gy + 80} x2={gx + 82} y2={gy + 10} stroke={C.red} strokeWidth={8} strokeLinecap="round" />);
  }
  return (
    <AbsoluteFill>
      <Grid />
      <div style={top(170)}>
        <Slam t={t} at={28.72} size={175}>Thousands</Slam>
        <Slam t={t} at={29.2} size={100}>of <Hi p={ramp(t, 29.45, 29.8)}>fake flights</Hi></Slam>
      </div>
      <svg viewBox="0 0 1080 1920" style={full}>{marks}</svg>
    </AbsoluteFill>
  );
};

/* 8  30.4–34.0  "Then it cracks. Right at the sharp corner of a window cutout." */
export const SCrack: React.FC<SP> = ({ s }) => {
  const t = useT(s);
  const dive = ramp(t, 30.32, 30.72, Easing.out(Easing.cubic));
  const sc = 0.4 + 0.6 * dive;
  const shake = t > 30.68 && t < 31.0 ? (random(`sh${Math.floor(t * 30)}`) - 0.5) * 26 : 0;
  const crack = ramp(t, 30.68, 31.05, Easing.out(Easing.quad));
  const rivets: React.ReactNode[] = [];
  for (let x = 80; x <= 1000; x += 38) { rivets.push(<circle key={`a${x}`} cx={x} cy={390} r={5} fill="#9CA4AB" />, <circle key={`b${x}`} cx={x} cy={1220} r={5} fill="#9CA4AB" />); }
  for (let y = 430; y <= 1190; y += 38) { rivets.push(<circle key={`c${y}`} cx={90} cy={y} r={5} fill="#9CA4AB" />, <circle key={`d${y}`} cx={990} cy={y} r={5} fill="#9CA4AB" />); }
  return (
    <AbsoluteFill>
      <div style={top(165)}>
        <Slam t={t} at={30.6} size={150} out={31.5}>Then it cracks</Slam>
      </div>
      <div style={{ ...top(165) }}>
        <Slam t={t} at={31.9} size={150}><Hi p={ramp(t, 32.25, 32.6)}>Sharp corner</Hi></Slam>
      </div>
      <svg viewBox="0 0 1080 1920" style={full}>
        <defs>
          <linearGradient id="skin" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#E4E7EA" /><stop offset="0.5" stopColor="#C9CED3" /><stop offset="1" stopColor="#AEB5BC" />
          </linearGradient>
        </defs>
        <g transform={`translate(${540 + shake} ${820 + shake * 0.6}) scale(${sc}) translate(-540 -820)`}>
          <rect x={50} y={350} width={980} height={910} rx={10} fill="url(#skin)" stroke="#7E868D" strokeWidth={4} filter="url(#shadow)" />
          {rivets}
          <rect x={330} y={560} width={420} height={470} rx={20} fill={C.glass} stroke="#7D858C" strokeWidth={10} />
          <polygon points="345,575 520,575 345,800" fill="#FFFFFF" opacity={0.08} />
          <Draw d="M 742 568 L 768 540 L 790 548 L 815 508 L 846 498 L 872 460 L 906 448 L 934 404 L 962 392" p={crack} stroke={C.ink} w={7} />
          <Draw d="M 815 508 L 826 470 L 852 450 L 860 418" p={ramp(t, 30.85, 31.15)} stroke={C.ink} w={5} />
          <Draw d={loopPath(748, 566, 130, 115)} p={ramp(t, 32.15, 32.6)} w={13} />
        </g>
      </svg>
    </AbsoluteFill>
  );
};

/* 9  34.0–40.0  "Here's why. Every flight, the cabin puffs up like a balloon, then shrinks when you land." */
export const SPuff: React.FC<SP> = ({ s }) => {
  const t = useT(s);
  const up = ramp(t, 36.6, 37.3), down = ramp(t, 38.5, 39.2);
  const R = 250 * (1 + 0.13 * (up - down)) * pop(t, 34.9, 13, 140);
  const dir = up > 0 && down < 0.05 ? 1 : -1;
  const arr = t > 36.6 ? (dir === 1 ? up : down) : 0;
  const cx = 540, cy = 880;
  return (
    <AbsoluteFill>
      <Grid />
      <div style={top(150)}><Slam t={t} at={34.2} size={150}>Here&apos;s why</Slam></div>
      <Tag t={t} at={35.1} x={540} y={385} rot={-2} size={56} out={36.5}>Every flight</Tag>
      <Tag t={t} at={36.62} x={540} y={385} rot={2} bg={C.yellow} size={56} out={38.4}>Climb: cabin puffs up</Tag>
      <Tag t={t} at={38.52} x={540} y={385} rot={-2} size={56}>Landing: it shrinks</Tag>
      <svg viewBox="0 0 1080 1920" style={full}>
        {t > 36.5 && <circle cx={cx} cy={cy} r={250} fill="none" stroke={C.ink} strokeWidth={4} strokeDasharray="14 14" opacity={0.6} />}
        <g filter="url(#shadow)">
          <circle cx={cx} cy={cy} r={R} fill="#F6F4EF" stroke={C.silver} strokeWidth={34} />
          <circle cx={cx} cy={cy} r={R + 17} fill="none" stroke="#7E868D" strokeWidth={4} />
        </g>
        {R > 10 && (
          <g>
            <line x1={cx - R * 0.93} y1={cy + R * 0.36} x2={cx + R * 0.93} y2={cy + R * 0.36} stroke="#8E979F" strokeWidth={10} />
            {[-0.55, -0.2, 0.2, 0.55].map((k, i) => (
              <path key={i} d={`M ${cx + k * R - 26} ${cy + R * 0.36} L ${cx + k * R - 26} ${cy + R * 0.1} L ${cx + k * R + 14} ${cy + R * 0.1} L ${cx + k * R + 18} ${cy - R * 0.12} L ${cx + k * R + 32} ${cy - R * 0.12} L ${cx + k * R + 30} ${cy + R * 0.36}`} fill={C.blue} opacity={0.85} />
            ))}
          </g>
        )}
        {Array.from({ length: 8 }).map((_, i) => {
          const a = (i / 8) * Math.PI * 2 + 0.39, r0 = R + 50, r1 = R + 140;
          const [a0, a1] = dir === 1 ? [r0, r1] : [r1, r0];
          const p = arr;
          return <Arrow key={i} a={[cx + Math.cos(a) * a0, cy + Math.sin(a) * a0]} b={[cx + Math.cos(a) * a1, cy + Math.sin(a) * a1]} bend={0.01} p={p} w={10} stroke={dir === 1 ? C.red : C.ink} />;
        })}
        <text x={540} y={1345} textAnchor="middle" fontFamily={SERIF_I} fontSize={34} fill={C.ink} opacity={t > 36.6 ? 0.7 : 0}>exaggerated, not to scale</text>
      </svg>
    </AbsoluteFill>
  );
};

/* 10  40.0–46.8  stress lines: curves spread it, corners pile it up */
const psi = (x: number, y: number, R: number, p: number) => {
  const r = p === 2 ? Math.hypot(x, y) : Math.pow(Math.pow(Math.abs(x), p) + Math.pow(Math.abs(y), p), 1 / p);
  return y * (1 - (R * R) / Math.max(r * r, 1e-6));
};
const streams = (R: number, p: number) => {
  const out: string[] = [];
  for (const y0 of [-160, -122, -86, -54, -24, 24, 54, 86, 122, 160]) {
    const sg = Math.sign(y0), pts: string[] = [];
    for (let x = -450; x <= 450; x += 6) {
      let lo = 0, hi = Math.abs(y0) + 3 * R;
      for (let it = 0; it < 40; it++) {
        const mid = (lo + hi) / 2;
        if (psi(x, mid, R, p) < Math.abs(y0)) lo = mid; else hi = mid;
      }
      pts.push(`${x} ${(sg * (lo + hi) / 2).toFixed(1)}`);
    }
    out.push("M" + pts.join(" L"));
  }
  return out;
};
const ROUND = streams(92, 2), SQUARE = streams(88, 9);
const Plate: React.FC<{ t: number; cy: number; lines: string[]; square?: boolean; k: number; hot?: number }> = ({ t, cy, lines, square, k, hot = 0 }) => (
  <g transform={`translate(540 ${cy}) scale(${k})`} opacity={k > 0.01 ? 1 : 0}>
    <defs>
      <clipPath id={`pl${square ? 1 : 0}`}><rect x={-450} y={-175} width={900} height={350} rx={8} /></clipPath>
      <radialGradient id="hot"><stop offset="0" stopColor={C.red} stopOpacity={0.95} /><stop offset="1" stopColor={C.red} stopOpacity={0} /></radialGradient>
    </defs>
    <rect x={-450} y={-175} width={900} height={350} rx={8} fill="#D3D7DB" stroke="#7E868D" strokeWidth={4} filter="url(#shadow)" />
    <g clipPath={`url(#pl${square ? 1 : 0})`}>
      {lines.map((d, i) => <path key={i} d={d} fill="none" stroke="#6E767D" strokeWidth={3} />)}
      {lines.map((d, i) => <path key={`f${i}`} d={d} fill="none" stroke={C.ink} strokeWidth={6} strokeDasharray="16 34" strokeDashoffset={-t * 150} strokeLinecap="round" />)}
      {hot > 0 && [[-88, -88], [88, -88], [-88, 88], [88, 88]].map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={70 + 20 * Math.sin(t * 8)} fill="url(#hot)" opacity={hot} />
      ))}
    </g>
    {square
      ? <rect x={-88} y={-88} width={176} height={176} rx={4} fill={C.paper} stroke={C.ink} strokeWidth={6} />
      : <circle r={92} fill={C.paper} stroke={C.ink} strokeWidth={6} />}
  </g>
);
export const SStress: React.FC<SP> = ({ s }) => {
  const t = useT(s);
  const kA = pop(t, 40.05, 14, 140), kB = pop(t, 43.72, 14, 160);
  const hot = ramp(t, 44.4, 45.5);
  return (
    <AbsoluteFill>
      <Grid />
      <div style={top(150)}><Slam t={t} at={40.2} size={150}>Stress flows</Slam></div>
      <svg viewBox="0 0 1080 1920" style={full}>
        <Plate t={t} cy={610} lines={ROUND} k={kA} />
        <Plate t={t} cy={1060} lines={SQUARE} square k={kB} hot={hot} />
        <Draw d={loopPath(628, 972, 80, 70)} p={ramp(t, 45.35, 45.8)} w={11} />
      </svg>
      <Tag t={t} at={42.46} x={330} y={405} rot={-4} bg={C.green} color="#FFFFFF" size={50}>Curve: spread out</Tag>
      <Tag t={t} at={43.75} x={330} y={855} rot={3} bg={C.red} color="#FFFFFF" size={50}>Corner: piles up</Tag>
    </AbsoluteFill>
  );
};

/* 11  46.8–51.4  "Flight after flight, the metal gets tired. Engineers call it metal fatigue." */
export const SDoc: React.FC<SP> = ({ s }) => {
  const t = useT(s);
  const k = pop(t, 46.85, 14, 130);
  const { rich } = useLook();
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 100, top: 230, width: 880, height: 1060, transform: `rotate(-2deg) scale(${k})` }}>
        {rich && <><Tape x="50%" y={0} rot={-3} w={220} /><Tape x="4%" y="98%" rot={42} w={150} /><Tape x="96%" y="98%" rot={-40} w={150} /></>}
        <div style={{ width: "100%", height: "100%", filter: rich ? "url(#cutx)" : "url(#cut)" }}>
        <div style={{ width: "100%", height: "100%", background: "#FBF8F1", padding: "64px 70px", boxSizing: "border-box" }}>
          <div style={{ fontFamily: OSWALD, fontWeight: 700, fontSize: 64, color: C.ink, letterSpacing: "0.02em" }}>WHAT IS METAL FATIGUE?</div>
          <div style={{ height: 6, background: C.ink, margin: "18px 0 34px" }} />
          <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginBottom: 14 }}>
            {Array.from({ length: 12 }).map((_, i) => {
              const at = 46.95 + i * 0.13;
              return (
                <svg key={i} width={52} height={52} viewBox="-50 -50 100 100" style={{ opacity: t > at ? 1 : 0, transform: `scale(${pop(t, at, 12, 260)})` }}>
                  <path d={PLANE} fill={i % 2 ? C.blue : C.ink} transform={`rotate(${i % 2 ? 20 : -20})`} />
                </svg>
              );
            })}
          </div>
          <div style={{ fontFamily: SERIF_I, fontSize: 30, color: "#555", marginBottom: 36 }}>one takeoff + one landing = one load cycle</div>
          <div style={{ fontFamily: SERIF, fontSize: 50, lineHeight: 1.55, color: C.ink }}>
            Every flight loads and unloads the cabin skin. Repeated loading, even well below the breaking point,
            {" "}<Hi p={ramp(t, 48.2, 48.9)}>slowly grows tiny cracks.</Hi>{" "}
            Engineers call this <Hi p={ramp(t, 50.3, 50.85)}><b>metal fatigue.</b></Hi>
          </div>
        </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* 12  51.4–53.9  "So now, every window is rounded." */
export const SRound: React.FC<SP> = ({ s }) => {
  const t = useT(s);
  const w = pop(t, 51.5, 13, 120);
  return (
    <AbsoluteFill>
      <div style={top(160)}>
        <Slam t={t} at={52.25} size={120}>Every window</Slam>
        <Slam t={t} at={53.05} size={190}><Hi p={ramp(t, 53.15, 53.5)}>Rounded</Hi></Slam>
      </div>
      <div style={{ position: "absolute", left: 310, top: 610, width: 460, height: 640, transform: `scale(${w}) rotate(2deg)` }}>
        <CutOut tape style={{ width: "100%", height: "100%" }}><WindowArt drift={t * 40} outline={ramp(t, 53.05, 53.8)} /></CutOut>
      </div>
    </AbsoluteFill>
  );
};

/* 13  53.9–60.0  "Next time you fly, look at your window. That curve isn't style. It's a lesson." */
export const SEnd: React.FC<SP> = ({ s }) => {
  const t = useT(s);
  const z = 1 + 0.12 * ramp(t, 53.9, 60, Easing.linear);
  const fade = ramp(t, 59.4, 60, Easing.linear);
  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 310, top: 610, width: 460, height: 640, transform: `scale(${z}) rotate(2deg)` }}>
        <CutOut tape style={{ width: "100%", height: "100%" }}><WindowArt drift={t * 40} outline={1 - ramp(t, 54.0, 54.5)} /></CutOut>
      </div>
      <svg viewBox="0 0 1080 1920" style={full}>
        <Arrow a={[930, 470]} b={[770, 640]} bend={-70} p={ramp(t, 55.2, 55.75)} w={13} />
      </svg>
      <div style={top(160)}>
        <Slam t={t} at={56.35} size={90}>That curve isn&apos;t style.</Slam>
        <Slam t={t} at={57.86} size={170}>It&apos;s a <Hi p={ramp(t, 58.05, 58.45)}>lesson.</Hi></Slam>
      </div>
      <AbsoluteFill style={{ background: C.ink, opacity: fade * 0.0 }} />
    </AbsoluteFill>
  );
};
