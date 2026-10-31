#!/usr/bin/env python3
"""Compose an ORIGINAL instrumental BGM in code (numpy + ffmpeg). Every --seed gives a different piece
(progression, motif, voicing, groove), so tracks don't sound like the over-used library music.
Usage: python3 compose.py public/music.wav --bpm 112 --bars 28 --drop 8 --key A --mode minor --seed 7 [--style pulse|calm]
Structure (bars): intro(pad) -> build(+arp, riser into drop) -> DROP at --drop (+drums, bass, motif) -> outro (last 2 bars, resolve).
The drop lands exactly on a downbeat, so plan the film's climax on bar --drop. Output is loudness-normalised to -14 LUFS.
"""
import argparse, json, os, re, subprocess, tempfile, wave
import numpy as np

SR = 44100
NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
SCALES = {"minor": [0, 2, 3, 5, 7, 8, 10], "major": [0, 2, 4, 5, 7, 9, 11]}
PROGS = {  # scale degrees (0-based), one chord per bar
    "minor": [[0, 5, 2, 6], [0, 3, 5, 4], [0, 6, 5, 6], [5, 6, 0, 0], [0, 5, 3, 4]],
    "major": [[0, 4, 5, 3], [0, 5, 3, 4], [3, 4, 0, 5], [0, 3, 4, 3]],
}

def hz(midi): return 440.0 * 2 ** ((midi - 69) / 12)

def tone(f, n, harm=6, bright=0.6, detune=0.0):
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, harm + 1):
        x += (bright ** (k - 1)) / k * np.sin(2 * np.pi * f * k * t * (1 + detune * (k % 2 * 2 - 1)))
    return x

def env(n, a, r):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)

def add(buf, x, at):
    i = int(at * SR)
    if i >= len(buf): return
    m = min(len(x), len(buf) - i)
    buf[i:i + m] += x[:m]

def reverb(x, seconds=1.6, mix=0.28, seed=0):
    r = np.random.default_rng(seed)
    n = int(seconds * SR)
    ir = r.normal(0, 1, n) * np.exp(-np.arange(n) / SR * 4.5)
    ir[: int(0.02 * SR)] = 0
    L = 1 << int(np.ceil(np.log2(len(x) + n)))
    wet = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[: len(x)]
    wet /= np.abs(wet).max() + 1e-9
    return (1 - mix) * x + mix * wet * np.abs(x).max()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--bpm", type=float, default=112); ap.add_argument("--bars", type=int, default=28)
    ap.add_argument("--drop", type=int, default=8); ap.add_argument("--key", default="A"); ap.add_argument("--mode", default="minor")
    ap.add_argument("--seed", type=int, default=1); ap.add_argument("--style", default="pulse", choices=["pulse", "calm"])
    ap.add_argument("--lufs", type=float, default=-14.0)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    beat = 60 / a.bpm; bar = 4 * beat
    total = a.bars * bar + 2.5
    N = int(total * SR)
    pad, keys, bass, drums, lead = (np.zeros(N) for _ in range(5))
    root = 57 + NOTE[a.key.upper()] - 9  # key root around A3
    sc = SCALES[a.mode]
    prog = PROGS[a.mode][rng.integers(len(PROGS[a.mode]))]
    deg = lambda d: root + sc[d % 7] + 12 * (d // 7)
    chord = lambda d: [deg(d), deg(d + 2), deg(d + 4), deg(d + 6) if rng.random() < 0.35 else deg(d + 7)]
    chords = [chord(prog[b % 4]) for b in range(a.bars)]
    chords[-1] = chord(0)  # resolve
    motif_len = 8  # eighth notes, 2 bars... built from pentatonic-ish scale degrees
    pent = [0, 2, 4, 5, 7] if a.mode == "major" else [0, 2, 3, 4, 6]
    motif = [int(rng.choice(pent)) + 7 * int(rng.random() < 0.3) for _ in range(motif_len)]
    rhythm = rng.choice([[1, 0, 1, 1, 0, 1, 0, 1], [1, 1, 0, 1, 0, 1, 1, 0], [1, 0, 0, 1, 1, 0, 1, 0]])
    arp_pat = rng.permutation(4)
    calm = a.style == "calm"
    for b in range(a.bars):
        t0 = b * bar
        c = chords[b]
        after = b >= a.drop
        outro = b >= a.bars - 2
        # pad: soft, detuned, swells
        n = int(bar * SR * 1.05)
        p = sum(tone(hz(m), n, 7, 0.55, 0.0015) for m in c[:3]) * env(n, 0.35 * bar, 3.0)
        add(pad, p * (0.9 if not after else 0.7), t0)
        # arp: from the build onwards (and in calm style throughout)
        if b >= min(a.drop - 4, 2) or calm:
            step = beat / (2 if not calm else 1)
            for k in range(int(bar / step)):
                m = c[arp_pat[k % 4]] + 12
                nn = int(0.9 * SR)
                add(keys, tone(hz(m), nn, 5, 0.45) * env(nn, 0.003, 0.35) * (0.55 if not outro else 0.35), t0 + k * step)
        if after and not outro:
            # bass on every beat (pulse) or half notes (calm)
            hits = range(4) if not calm else (0, 2)
            for k in hits:
                nn = int(beat * SR * (0.95 if not calm else 1.9))
                add(bass, tone(hz(c[0] - 12), nn, 3, 0.3) * env(nn, 0.004, 0.45), t0 + k * beat)
            if not calm:
                for k in range(4):  # kick on every beat, accent on downbeat
                    nn = int(0.35 * SR); tt = np.arange(nn) / SR
                    kick = np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-tt * 30)) / SR) * env(nn, 0.001, 0.12)
                    add(drums, kick * (1.0 if k == 0 else 0.75), t0 + k * beat)
                for k in (1, 3):  # clap
                    nn = int(0.2 * SR)
                    cl = np.diff(rng.normal(0, 1, nn + 1)) * env(nn, 0.001, 0.05)
                    add(drums, cl * 0.25, t0 + k * beat)
                for k in range(8):  # hats
                    nn = int(0.06 * SR)
                    hh = np.diff(np.diff(rng.normal(0, 1, nn + 2))) * env(nn, 0.0005, 0.015)
                    add(drums, hh * (0.08 if k % 2 else 0.05), t0 + k * beat / 2)
            # motif: 2-bar phrase, transposed with the chord, varied every other phrase
            if (b - a.drop) % 2 == 0:
                for k, on in enumerate(rhythm):
                    if not on: continue
                    d = prog[b % 4] + motif[k] + (1 if ((b - a.drop) // 2) % 2 and k == 7 else 0)
                    nn = int(1.2 * SR)
                    add(lead, tone(hz(deg(d) + 12), nn, 4, 0.35) * env(nn, 0.01, 0.6), t0 + k * beat / 2 * 2)
    # riser into the drop
    if a.drop >= 2:
        dur = 2 * beat; nn = int(dur * SR); tt = np.arange(nn) / SR
        noise = np.diff(rng.normal(0, 1, nn + 1))
        riser = noise * (tt / dur) ** 2.2 * 0.35 + np.sin(2 * np.pi * np.cumsum(200 * 8 ** (tt / dur)) / SR) * (tt / dur) ** 2 * 0.15
        add(drums, riser, a.drop * bar - dur)
        # downbeat impact
        nn = int(1.5 * SR); tt = np.arange(nn) / SR
        add(drums, np.sin(2 * np.pi * np.cumsum(35 + 70 * np.exp(-tt * 8)) / SR) * env(nn, 0.002, 0.45) * 0.9, a.drop * bar)
    mix = 0.55 * reverb(pad, 2.2, 0.35, a.seed) + 0.5 * reverb(keys, 1.4, 0.3, a.seed + 1) + 0.6 * bass + 0.55 * drums + 0.45 * reverb(lead, 1.8, 0.35, a.seed + 2)
    # dynamics: the intro/build sits well below the drop so the drop actually opens up
    gain = np.ones(N); d0 = int(a.drop * bar * SR)
    gain[:d0] = np.linspace(0.32, 0.5, d0) if d0 > 0 else gain[:d0]
    o0 = int((a.bars - 2) * bar * SR); gain[o0:] = np.linspace(0.6, 0.45, N - o0)
    mix *= gain
    # gentle fade at the very end (music, not silence, carries the last bar)
    fade = int(2.0 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
    mix = np.tanh(mix / (np.abs(mix).max() + 1e-9) * 1.15) * 0.9
    st = np.stack([mix, np.roll(mix, int(0.012 * SR)) * 0.96 + mix * 0.04], 1)  # light stereo width
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    with wave.open(tmp, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    # two-step loudness: measure, apply exact gain, then a brick-wall limiter at about -1.5 dBFS
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", tmp, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    I = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", meas)[-1])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", f"volume={a.lufs - I:.2f}dB,alimiter=limit=0.84:level=false",
                    "-ar", str(SR), a.out], check=True)
    os.unlink(tmp)
    # exact beat grid: we wrote the music, so no detection is needed (prepare.py uses this file if present)
    grid = {"bpm": a.bpm, "meter": 4, "offset_s": 0.0, "bars": a.bars, "drop_bar": a.drop, "drop_s": round(a.drop * bar, 3),
            "key": a.key, "mode": a.mode, "seed": a.seed, "style": a.style}
    with open(os.path.splitext(a.out)[0] + ".grid.json", "w") as f:
        json.dump(grid, f, indent=1)
    print(f"wrote {a.out}: {a.bpm} BPM, {a.bars} bars ({a.bars * bar:.1f}s), drop at bar {a.drop} = {a.drop * bar:.2f}s, "
          f"{a.key} {a.mode}, progression {prog}, seed {a.seed}, style {a.style}")

if __name__ == "__main__":
    main()
