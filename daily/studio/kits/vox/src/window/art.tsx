import React from "react";
import { C } from "./ui";

/** de Havilland Comet 1 side view, drawn in a 1000 x 260 box (generic silver, no airline livery) */
export const CometG: React.FC<{ wing?: boolean; uid?: string }> = ({ wing = true, uid = "a" }) => {
  const body = "M 150 104 L 800 104 L 968 94 L 972 112 C 930 128, 880 150, 800 156 L 150 156 C 90 156, 46 150, 40 132 C 48 112, 95 104, 150 104 Z";
  const wins: React.ReactNode[] = [];
  for (let x = 196; x <= 770; x += 40) wins.push(<rect key={x} x={x} y={113} width={22} height={19} rx={4} fill={C.glass} />);
  return (
    <g>
      <defs>
        <linearGradient id={`cb${uid}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#FAFAF8" /><stop offset="0.55" stopColor="#E9EBEC" /><stop offset="1" stopColor="#B9BFC5" />
        </linearGradient>
        <clipPath id={`cc${uid}`}><path d={body} /></clipPath>
      </defs>
      {wing && <path d="M 392 150 L 575 150 L 735 222 L 680 228 Z" fill="#AEB5BC" stroke="#7E868D" strokeWidth={2} />}
      <path d="M 820 106 L 902 20 L 948 20 L 952 98 Z" fill={`url(#cb${uid})`} stroke="#7E868D" strokeWidth={2} />
      <path d="M 862 100 L 992 90 L 996 99 L 872 110 Z" fill="#C9CED3" stroke="#7E868D" strokeWidth={2} />
      <path d={body} fill={`url(#cb${uid})`} stroke="#7E868D" strokeWidth={2.5} />
      <g clipPath={`url(#cc${uid})`}>
        <rect x={30} y={136} width={960} height={7} fill={C.blue} />
        <rect x={30} y={146} width={960} height={14} fill="#AAB1B8" opacity={0.6} />
      </g>
      {wins}
      <path d="M 66 120 L 92 112 L 98 124 L 72 128 Z" fill={C.glass} />
      <path d="M 102 110 L 128 108 L 130 121 L 104 123 Z" fill={C.glass} />
      {wing && <ellipse cx={402} cy={150} rx={20} ry={8} fill="#3B444C" />}
      <path d="M 152 108 L 790 108" stroke="#FFFFFF" strokeWidth={3} opacity={0.8} />
    </g>
  );
};

export const CometArt: React.FC<{ width: number; wing?: boolean; uid?: string }> = ({ width, wing, uid }) => (
  <svg viewBox="0 0 1000 260" width={width} height={width * 0.26} style={{ overflow: "visible" }}>
    <CometG wing={wing} uid={uid} />
  </svg>
);

/** airplane cabin window in a 400 x 560 box; square = old sharp-cornered look. outline = yellow trace 0..1 */
export const WindowArt: React.FC<{ square?: boolean; drift?: number; outline?: number }> = ({ square = false, drift = 0, outline = 0 }) => {
  const id = square ? "sq" : "rd";
  const rIn = square ? 10 : 125, rBev = square ? 16 : 145, rOut = square ? 30 : 175;
  const cl = (x: number, y: number, s: number) => {
    const xx = ((x + drift) % 520) - 60;
    return (
      <g transform={`translate(${xx} ${y}) scale(${s})`} opacity={0.95}>
        <ellipse cx={0} cy={0} rx={60} ry={22} fill="#FFFFFF" />
        <ellipse cx={-30} cy={-14} rx={34} ry={22} fill="#FFFFFF" />
        <ellipse cx={22} cy={-18} rx={30} ry={24} fill="#FFFFFF" />
      </g>
    );
  };
  return (
    <svg viewBox="0 0 400 560" width="100%" height="100%" style={{ overflow: "visible" }}>
      <defs>
        <linearGradient id={`sky${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#5E98CF" /><stop offset="0.7" stopColor="#A9D0EE" /><stop offset="1" stopColor="#DDEEF9" />
        </linearGradient>
        <linearGradient id={`fr${id}`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#F3EEE4" /><stop offset="1" stopColor="#D9D1C1" />
        </linearGradient>
        <clipPath id={`clip${id}`}><rect x={70} y={70} width={260} height={420} rx={rIn} /></clipPath>
      </defs>
      <rect x={8} y={8} width={384} height={544} rx={rOut} fill={`url(#fr${id})`} stroke="#BDB3A0" strokeWidth={4} />
      <rect x={46} y={46} width={308} height={468} rx={rBev} fill="#CFC6B3" />
      <g clipPath={`url(#clip${id})`}>
        <rect x={70} y={70} width={260} height={420} fill={`url(#sky${id})`} />
        {cl(80, 170, 1)}{cl(300, 260, 0.7)}{cl(190, 360, 1.2)}
        <polygon points="30,500 420,372 420,520 30,520" fill="#B5BBC1" />
        <polygon points="30,500 420,372 420,384 30,512" fill="#8F979E" />
        <polygon points="70,70 190,70 70,300" fill="#FFFFFF" opacity={0.18} />
      </g>
      <rect x={70} y={70} width={260} height={420} rx={rIn} fill="none" stroke="#8E8676" strokeWidth={6} />
      {outline > 0.001 && (
        <rect x={62} y={62} width={276} height={436} rx={rIn + 8} fill="none" stroke={C.yellow} strokeWidth={16}
          pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - outline} strokeLinecap="round" />
      )}
    </svg>
  );
};

/** small top-view plane pointing right, centred on 0,0 */
export const PLANE = "M 42 0 L 12 -5 L 2 -32 L -7 -32 L -2 -5 L -26 -4 L -34 -15 L -41 -15 L -37 0 L -41 15 L -34 15 L -26 4 L -2 5 L -7 32 L 2 32 L 12 5 Z";
