#!/usr/bin/env python3
"""Synthesize a small SFX library with code (numpy only). 44.1 kHz 16-bit mono WAVs.
Usage: python3 sfx.py public/sfx [--key A]
Makes: whoosh, pop, tick, thud, boom, riser, shimmer, glitch, typing, note_1..note_8
(note_N = ascending bell/pluck scale in --key, for "each step up = higher note").
"""
import argparse, os, wave
import numpy as np

SR = 44100
rng = np.random.default_rng(7)
t_ = lambda d: np.arange(int(SR * d)) / SR

def env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / r)

def lowpass(x, cutoff):  # one-pole, cutoff may be array
    c = np.broadcast_to(np.asarray(cutoff, float), x.shape)
    k = 1 - np.exp(-2 * np.pi * c / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)):
        s += k[i] * (x[i] - s); y[i] = s
    return y

def norm(x, peak=0.8):
    x = x - x.mean()
    fade = min(len(x), 256); x[-fade:] *= np.linspace(1, 0, fade)
    return x / (np.abs(x).max() + 1e-9) * peak

def whoosh(d=0.45):
    t = t_(d); n = rng.normal(0, 1, len(t))
    sweep = 300 + 5000 * np.sin(np.pi * t / d) ** 2
    return lowpass(n, sweep) * np.sin(np.pi * t / d) ** 1.5

def pop(d=0.12):
    t = t_(d); f = 900 * np.exp(-t * 25) + 300
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.001, 0.03)

def tick(d=0.04):
    t = t_(d); return (np.sin(2 * np.pi * 3200 * t) + 0.5 * rng.normal(0, 1, len(t))) * env(len(t), 0.0005, 0.006)

def thud(d=0.5):
    t = t_(d); f = 40 + 110 * np.exp(-t * 18)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(t), 0.002, 0.15)

def boom(d=1.6):
    t = t_(d); low = np.sin(2 * np.pi * np.cumsum(35 + 60 * np.exp(-t * 6)) / SR)
    noise = lowpass(lowpass(rng.normal(0, 1, len(t)), 300), 300) * 6
    return (low + noise) * env(len(t), 0.003, 0.5)

def riser(d=1.5):
    t = t_(d); f = 200 * (12 ** (t / d))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.4
    noise = lowpass(rng.normal(0, 1, len(t)), 500 + 7000 * t / d)
    return (tone + noise) * (t / d) ** 2

def bell(freq, d=1.2, bright=1.0):
    t = t_(d); x = np.zeros_like(t)
    for ratio, amp, dec in [(1, 1, 0.9), (2.0, 0.5, 0.5), (3.01, 0.25 * bright, 0.3), (4.2, 0.15 * bright, 0.15)]:
        x += amp * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-t / (dec * d / 1.2))
    return x * env(len(t), 0.002, 10)

def shimmer(d=1.4):
    t = t_(d); x = np.zeros_like(t)
    for k, f in enumerate([1318.5, 1567.98, 1975.5, 2637.0]):
        s = int(k * 0.06 * SR); b = bell(f, d - k * 0.06, 0.5)
        n = min(len(b), len(x) - s); x[s:s + n] += b[:n] * 0.5
    return x

def glitch(d=0.25):
    t = t_(d); sq = np.sign(np.sin(2 * np.pi * rng.choice([180, 360, 720], len(t) // 800 + 1).repeat(800)[: len(t)] * t))
    return sq * (rng.random(len(t) // 600 + 1).repeat(600)[: len(t)] > 0.4) * env(len(t), 0.001, 0.12)

def typing(d=0.6, hits=6):
    x = np.zeros(int(SR * d))
    for i in range(hits):
        s = int((i * d / hits + rng.uniform(0, 0.02)) * SR); c = tick() * rng.uniform(0.5, 1)
        x[s:s + len(c)] += c[: len(x) - s]
    return x

KEYS = {"C": 261.63, "D": 293.66, "E": 329.63, "F": 349.23, "G": 392.0, "A": 440.0, "B": 493.88}
MAJOR = [0, 2, 4, 5, 7, 9, 11, 12]

def write(path, x):
    x = norm(x)
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("outdir"); ap.add_argument("--key", default="C")
    a = ap.parse_args(); os.makedirs(a.outdir, exist_ok=True)
    lib = dict(whoosh=whoosh(), pop=pop(), tick=tick(), thud=thud(), boom=boom(), riser=riser(),
               shimmer=shimmer(), glitch=glitch(), typing=typing())
    root = KEYS[a.key.upper()]
    for i, semi in enumerate(MAJOR, 1):
        lib[f"note_{i}"] = bell(root * 2 ** (semi / 12), 1.0)
    for name, x in lib.items():
        write(os.path.join(a.outdir, f"{name}.wav"), x)
    print("wrote", len(lib), "sfx to", a.outdir, ":", ", ".join(lib))

if __name__ == "__main__":
    main()
