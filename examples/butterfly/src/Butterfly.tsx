import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  interpolate,
  random,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { AUDIO, BEAT, DOWN, Scene, SceneSpec, beatsIn, layout } from "./timeline";

// ---------- style tokens ----------
const SERIF =
  '"Noto Serif SC","Source Han Serif SC","Source Han Serif CN","思源宋体","STZhongsong","SimSun",serif';
const SANS = '"Segoe UI","Inter","Microsoft YaHei",sans-serif';
const GOLD = "#d9b45a";
const IVORY = "#f3e9d2";
const DIM = "rgba(243,233,210,0.45)";
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);
const easeInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

// ---------- script: one row per shot; caption 【...】 = gold highlight ----------
const SPECS: SceneSpec[] = [
  { id: "title", bars: 1 },
  { id: "wings", bars: 1, caption: "一只蝴蝶，扇了扇翅膀", sfx: [{ at: 0, name: "whoosh", volume: 0.5 }] },
  { id: "paper", bars: 1, caption: "一张纸，厚【0.1 毫米】", sfx: [{ at: 0, name: "pop", volume: 0.7 }] },
  { id: "fold", bars: 1, caption: "每对折一次，厚度翻一倍" },
  { id: "moon", bars: 2, caption: "对折 42 次，比【地球到月亮】还远", sfx: [{ at: 0, name: "boom", volume: 0.8 }] },
];

const raw = layout(SPECS);
// beat-locked SFX that depend on the measured grid
export const SCENES: Scene[] = raw.map((s) => {
  const b = beatsIn(s);
  if (s.id === "title") {
    const hit = b.find((f) => f >= 6) ?? 12;
    return { ...s, sfx: [{ at: hit, name: "shimmer", volume: 0.55 }] };
  }
  if (s.id === "fold") {
    const notes = b.slice(0, 4).map((f, i) => ({ at: f, name: `note_${i + 1}`, volume: 0.55 }));
    return { ...s, sfx: [...notes, { at: Math.max(0, s.duration - 45), name: "riser", volume: 0.45 }] };
  }
  if (s.id === "moon") {
    return { ...s, sfx: [...(s.sfx ?? []), { at: s.duration - 40, name: "shimmer", volume: 0.5 }] };
  }
  return s;
});
const last = SCENES[SCENES.length - 1];
export const TOTAL = last.from + last.duration;

// ---------- shared pieces ----------
const Background: React.FC = () => {
  const f = useCurrentFrame();
  const dots = new Array(70).fill(0).map((_, i) => {
    const x = random(`x${i}`) * 1920;
    const y = (random(`y${i}`) * 1180 - f * (0.15 + random(`s${i}`) * 0.35)) % 1180;
    const o = 0.15 + 0.35 * random(`o${i}`) * (0.6 + 0.4 * Math.sin(f / 20 + i));
    return <circle key={i} cx={x} cy={y < 0 ? y + 1180 : y} r={0.8 + random(`r${i}`) * 1.6} fill={GOLD} opacity={o} />;
  });
  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, #182033 0%, #0b0f1a 55%, #05070c 100%)" }}>
      <svg width={1920} height={1080}>{dots}</svg>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px rgba(0,0,0,0.85)" }} />
    </AbsoluteFill>
  );
};

const Hud: React.FC = () => {
  const s: React.CSSProperties = { position: "absolute", fontFamily: SANS, fontSize: 18, letterSpacing: 6, color: DIM };
  const corner = (pos: React.CSSProperties) => (
    <div style={{ position: "absolute", width: 34, height: 34, borderColor: "rgba(217,180,90,0.5)", borderStyle: "solid", borderWidth: 0, ...pos }} />
  );
  return (
    <AbsoluteFill>
      <div style={{ ...s, left: 70, top: 52 }}>MY OWN FILM</div>
      <div style={{ ...s, right: 70, top: 52 }}>1920 × 1080 · 30 FPS</div>
      {corner({ left: 48, top: 40, borderLeftWidth: 1.5, borderTopWidth: 1.5 })}
      {corner({ right: 48, top: 40, borderRightWidth: 1.5, borderTopWidth: 1.5 })}
      {corner({ left: 48, bottom: 40, borderLeftWidth: 1.5, borderBottomWidth: 1.5 })}
      {corner({ right: 48, bottom: 40, borderRightWidth: 1.5, borderBottomWidth: 1.5 })}
    </AbsoluteFill>
  );
};

const Caption: React.FC<{ text: string }> = ({ text }) => {
  const f = useCurrentFrame();
  const o = interpolate(f, [0, 8], [0, 1], clamp);
  const y = interpolate(f, [0, 10], [14, 0], clamp);
  const parts = text.split(/(【[^】]*】)/).filter(Boolean);
  return (
    <div style={{ position: "absolute", bottom: 120, width: "100%", textAlign: "center", fontFamily: SERIF, fontSize: 54,
      letterSpacing: 6, color: IVORY, opacity: o, transform: `translateY(${y}px)`, textShadow: "0 2px 18px rgba(0,0,0,0.8)" }}>
      {parts.map((p, i) =>
        p.startsWith("【") ? <span key={i} style={{ color: GOLD }}>{p.slice(1, -1)}</span> : <span key={i}>{p}</span>,
      )}
    </div>
  );
};

// ---------- shots ----------
const Title: React.FC<{ hit: number }> = ({ hit }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const chars = "蝴蝶效应".split("");
  const line = spring({ frame: f - hit, fps, config: { damping: 200 }, durationInFrames: 24 });
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ display: "flex", gap: 46 }}>
        {chars.map((c, i) => {
          const t = interpolate(f, [i * 3, i * 3 + 16], [0, 1], clamp);
          return (
            <span key={c} style={{ fontFamily: SERIF, fontSize: 132, color: IVORY, opacity: t,
              filter: `blur(${(1 - t) * 12}px)`, transform: `translateY(${(1 - easeOut(t)) * 24}px)` }}>{c}</span>
          );
        })}
      </div>
      <div style={{ position: "relative", width: 760, height: 40, marginTop: 30 }}>
        <div style={{ position: "absolute", top: 20, left: 380 - 380 * line, width: 760 * line, height: 1.5,
          background: `linear-gradient(90deg, transparent, ${GOLD}, transparent)` }} />
        {[-1, 1].map((d) => (
          <div key={d} style={{ position: "absolute", top: 16, left: 376 + d * 380 * line, width: 8, height: 8, borderRadius: 4,
            background: IVORY, boxShadow: `0 0 18px 6px ${GOLD}`, opacity: line }} />
        ))}
      </div>
      <div style={{ fontFamily: SANS, fontSize: 20, letterSpacing: 14, color: DIM, marginTop: 8, opacity: line }}>
        THE BUTTERFLY EFFECT
      </div>
    </AbsoluteFill>
  );
};

// polar butterfly curve -> particle wings
const WING_PTS = new Array(900).fill(0).map((_, i) => {
  const th = (i / 900) * 12 * Math.PI;
  const r = Math.exp(Math.sin(th)) - 2 * Math.cos(4 * th) + Math.pow(Math.sin((2 * th - Math.PI) / 24), 5);
  return { x: r * Math.sin(th), y: -r * Math.cos(th), j: random(`w${i}`) };
});

const Wings: React.FC<{ beats: number[] }> = ({ beats }) => {
  const f = useCurrentFrame();
  const flap = beats.length ? beats[Math.min(1, beats.length - 1)] : 30; // big flap on the 2nd beat
  const k = f < flap ? 0 : (f - flap) / 6;
  const fold = f < flap ? 0.92 + 0.08 * Math.cos(f / 5) : 0.35 + 0.65 * Math.abs(Math.cos(k));
  const build = interpolate(f, [0, 18], [0, 1], clamp);
  const ring = interpolate(f, [flap, flap + 40], [0, 1], clamp);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <svg width={1920} height={1080} viewBox="-960 -540 1920 1080">
        {ring > 0 && ring < 1 && [0, 0.25].map((d) => (
          <circle key={d} cx={0} cy={-40} r={60 + (ring - d) * 520} fill="none" stroke={GOLD} strokeWidth={1.2}
            opacity={Math.max(0, (1 - ring) * 0.7 - d)} />
        ))}
        <g transform={`translate(0,-40) scale(${78 * fold},78)`}>
          {WING_PTS.map((p, i) =>
            p.j < build ? <circle key={i} cx={p.x} cy={p.y} r={0.022 + p.j * 0.02} fill={i % 7 ? IVORY : GOLD} opacity={0.35 + p.j * 0.5} /> : null,
          )}
        </g>
      </svg>
    </AbsoluteFill>
  );
};

const Paper: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 14, mass: 0.7 } });
  const rot = interpolate(f, [0, 60], [-28, -18], clamp);
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", perspective: 1400 }}>
      <div style={{ width: 520, height: 340, transform: `translateY(-60px) rotateX(58deg) rotateZ(${rot}deg) scale(${s})`,
        background: "linear-gradient(135deg, #f7e6b0, #c9a24c)", boxShadow: `0 40px 80px rgba(0,0,0,0.6), 0 0 60px rgba(217,180,90,0.25)`,
        borderRadius: 4 }} />
      <div style={{ position: "absolute", left: 1290, top: 380, fontFamily: SANS, color: GOLD, fontSize: 26, letterSpacing: 4,
        opacity: interpolate(f, [12, 22], [0, 1], clamp) }}>
        <div style={{ width: 1.5, height: 70, background: GOLD, marginBottom: 10 }} />
        0.1 mm
      </div>
    </AbsoluteFill>
  );
};

const Fold: React.FC<{ beats: number[] }> = ({ beats }) => {
  const f = useCurrentFrame();
  const steps = beats.slice(0, 4);
  const n = steps.filter((b) => f >= b).length; // folds done so far
  const layers = Math.pow(2, n);
  const pulse = n > 0 ? interpolate(f - steps[n - 1], [0, 8], [1.12, 1], clamp) : 1;
  const mm = (0.1 * layers).toFixed(1);
  const H = 14 * layers; // stack height in px
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div style={{ position: "relative", width: 560, height: 420, transform: `scale(${pulse})` }}>
        {new Array(layers).fill(0).map((_, i) => (
          <div key={i} style={{ position: "absolute", left: 60 + (i % 2) * 6, bottom: 120 + (i * H) / layers, width: 440,
            height: Math.max(2, H / layers - 3), background: i % 2 ? "#e9cf8b" : "#c9a24c", borderRadius: 2,
            boxShadow: "0 2px 8px rgba(0,0,0,0.5)" }} />
        ))}
        <div style={{ position: "absolute", right: -40, bottom: 120, width: 1.5, height: H, background: GOLD }} />
        <div style={{ position: "absolute", right: -230, bottom: 110 + H / 2, fontFamily: SANS, fontSize: 44, color: GOLD,
          fontVariantNumeric: "tabular-nums" }}>{mm} mm</div>
        <div style={{ position: "absolute", left: 60, bottom: 60, fontFamily: SANS, fontSize: 22, letterSpacing: 6, color: DIM }}>
          FOLD × {n}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Moon: React.FC<{ dur: number }> = ({ dur }) => {
  const f = useCurrentFrame();
  const t = easeInOut(interpolate(f, [0, dur * 0.7], [0, 1], clamp));
  // log-scale roll from 1.6 mm to 439,804 km (0.1mm * 2^42)
  const mm = Math.pow(10, interpolate(t, [0, 1], [Math.log10(1.6), Math.log10(4.398e11)]));
  const label = mm < 1000 ? `${mm.toFixed(1)} mm` : mm < 1e6 ? `${(mm / 1000).toFixed(1)} m` : `${Math.round(mm / 1e6).toLocaleString("en-US")} km`;
  const barH = interpolate(t, [0, 1], [10, 700]);
  const moonO = interpolate(f, [dur * 0.45, dur * 0.7], [0, 1], clamp);
  const flash = interpolate(f, [0, 6, 20], [0.35, 0.15, 0], clamp);
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: GOLD, opacity: flash }} />
      <svg width={1920} height={1080}>
        <defs>
          <radialGradient id="earth"><stop offset="0%" stopColor="#3b6ea8" /><stop offset="100%" stopColor="#0d1f3a" /></radialGradient>
          <radialGradient id="moon"><stop offset="0%" stopColor="#f3ead2" /><stop offset="100%" stopColor="#8d8572" /></radialGradient>
        </defs>
        <circle cx={760} cy={900} r={70} fill="url(#earth)" stroke="rgba(120,170,230,0.5)" strokeWidth={2} />
        <rect x={757} y={830 - barH} width={6} height={barH} fill={GOLD} opacity={0.9} />
        <circle cx={760} cy={130} r={34} fill="url(#moon)" opacity={moonO} />
        <text x={810} y={140} fill={DIM} fontFamily={SANS} fontSize={22} letterSpacing={4} opacity={moonO}>MOON · 384,400 km</text>
      </svg>
      <div style={{ position: "absolute", left: 900, top: 470, fontFamily: SANS, fontSize: 84, fontWeight: 600, color: IVORY,
        fontVariantNumeric: "tabular-nums", letterSpacing: 2 }}>{label}</div>
      <div style={{ position: "absolute", left: 904, top: 580, fontFamily: SANS, fontSize: 22, letterSpacing: 6, color: DIM }}>
        0.1 mm × 2⁴²
      </div>
    </AbsoluteFill>
  );
};

const View: React.FC<{ s: Scene }> = ({ s }) => {
  const b = beatsIn(s);
  switch (s.id) {
    case "title": return <Title hit={(s.sfx ?? [])[0]?.at ?? 12} />;
    case "wings": return <Wings beats={b} />;
    case "paper": return <Paper />;
    case "fold": return <Fold beats={b} />;
    case "moon": return <Moon dur={s.duration} />;
    default: return null;
  }
};

export const Butterfly: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "#05070c" }}>
    <Background />
    <Audio src={staticFile(AUDIO)}
      volume={(f) => 0.75 * interpolate(f, [TOTAL - 15, TOTAL], [1, 0], clamp)} />
    {SCENES.map((s) => (
      <Sequence key={s.id} from={s.from} durationInFrames={s.duration} name={s.id}>
        <View s={s} />
        {s.caption ? <Caption text={s.caption} /> : null}
        {(s.sfx ?? []).map((x, i) => (
          <Sequence key={i} from={x.at} name={`sfx ${x.name}`}>
            <Audio src={staticFile(`sfx/${x.name}.wav`)} volume={x.volume ?? 0.6} />
          </Sequence>
        ))}
      </Sequence>
    ))}
    <Hud />
  </AbsoluteFill>
);

// keep exported for debugging overlays
export const GRID = { DOWN, BEAT };
