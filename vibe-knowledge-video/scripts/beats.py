#!/usr/bin/env python3
"""Detect BPM, beats and downbeats (重拍) of a music file. Needs only numpy + ffmpeg.
Usage: python3 beats.py music.mp3 --fps 30 [--bpm-hint 113] [--meter 4] [--phase 0-3] > beats.json
"""
import argparse, json, subprocess, sys
import numpy as np

SR, HOP, NFFT = 22050, 128, 1024
LAT = 0.0  # audio is front-padded by NFFT/2, so frame i is centred at i*HOP

def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)

def stft_mag(y):
    n = 1 + (len(y) - NFFT) // HOP
    idx = np.arange(NFFT)[None, :] + HOP * np.arange(n)[:, None]
    return np.abs(np.fft.rfft(y[idx] * np.hanning(NFFT), axis=1))

def onset_env(S, lo_hz=0, hi_hz=SR / 2):
    f = np.fft.rfftfreq(NFFT, 1 / SR)
    band = (f >= lo_hz) & (f < hi_hz)
    L = np.log1p(100 * S[:, band])
    flux = np.maximum(0, np.diff(L, axis=0)).sum(1)
    flux = np.concatenate([[0], flux])
    flux -= np.convolve(flux, np.ones(16) / 16, mode="same")  # remove slow trend
    flux = np.maximum(flux, 0)
    return flux / (flux.std() + 1e-9)

def tempo(env, fr, hint=None):
    ac = np.correlate(env, env, "full")[len(env) - 1:]
    bpms = np.arange(60, 200.01, 0.1)
    lags = 60 * fr / bpms
    score = np.interp(lags, np.arange(len(ac)), ac)
    # add harmonics (2x lag) so the true pulse beats its half/double
    score += 0.5 * np.interp(2 * lags, np.arange(len(ac)), ac)
    center = hint or 115
    score *= np.exp(-0.5 * (np.log2(bpms / center) / 0.9) ** 2)
    return float(bpms[np.argmax(score)])

def track(env, fr, bpm, tight=100):
    period = 60 * fr / bpm
    n = len(env)
    score = env.copy(); back = np.full(n, -1)
    win = np.arange(-int(2 * period), -int(period / 2))
    penalty = -tight * np.log(-win / period) ** 2
    for i in range(n):
        j = i + win; ok = j >= 0
        if ok.any():
            cand = score[j[ok]] + penalty[ok]
            k = np.argmax(cand)
            if cand[k] > 0:
                score[i] += cand[k]; back[i] = j[ok][k]
    # last beat: highest score in final period
    tail = np.arange(max(0, n - int(period)), n)
    i = tail[np.argmax(score[tail])]
    beats = []
    while i >= 0:
        beats.append(i); i = back[i]
    return np.array(beats[::-1])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio"); ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--bpm-hint", type=float); ap.add_argument("--meter", type=int, default=4)
    ap.add_argument("--phase", type=int, help="force which beat (0..meter-1) is the downbeat")
    a = ap.parse_args()
    y = load(a.audio); fr = SR / HOP
    S = stft_mag(np.concatenate([np.zeros(NFFT // 2 + 4 * HOP, np.float32), y]))[4:]
    env = onset_env(S)
    bpm = tempo(env, fr, a.bpm_hint)
    b = track(env, fr, bpm)
    # drop beats the tracker extrapolated into silent intro/outro
    loud = np.array([env[max(0, i - 3):i + 4].max() for i in b])
    real = np.where(loud > 0.25 * np.median(loud))[0]
    if len(real): b = b[real[0]:real[-1] + 1]
    times = b / fr + LAT
    if len(times) > 4:  # least-squares fit beat grid -> precise BPM
        bpm = float(60 / np.polyfit(np.arange(len(times)), times, 1)[0])
    # downbeat phase = phase whose beats carry most low-frequency (kick/bass) energy
    f_ = np.fft.rfftfreq(NFFT, 1 / SR)
    low = S[:, f_ < 150].sum(1)  # linear energy keeps loud-vs-soft kick difference
    w = int(0.05 * fr)
    strength = np.array([low[i:i + 2 * w + 1].max() - low[max(0, i - 3 * w):i].min(initial=0) for i in b])
    phase = int(np.argmax([strength[p::a.meter].mean() for p in range(a.meter)])) if a.phase is None else a.phase
    down = times[phase::a.meter]
    # accents: strongest 25% onsets anywhere (for SFX ideas), snapped to frames
    full = onset_env(S)
    peaks = [i for i in range(1, len(full) - 1) if full[i] > full[i - 1] and full[i] >= full[i + 1]]
    thr = np.percentile([full[i] for i in peaks], 75) if peaks else 0
    accents = [round(i / fr + LAT, 3) for i in peaks if full[i] >= thr]
    f = lambda t: int(round(t * a.fps))
    out = {
        "duration_s": round(len(y) / SR, 3), "fps": a.fps, "bpm": round(bpm, 1),
        "beat_interval_s": round(60 / bpm, 4), "meter": a.meter,
        "beats_s": [round(t, 3) for t in times], "downbeats_s": [round(t, 3) for t in down],
        "downbeat_frames": [f(t) for t in down], "beat_frames": [f(t) for t in times],
        "accents_s": accents,
        "bpm_alternatives": [round(bpm / 2, 1), round(bpm * 2, 1)],
        "note": "If bpm feels 2x too fast/slow, rerun with --bpm-hint <half or double>",
    }
    json.dump(out, sys.stdout, indent=1)
    print(f"\nBPM {out['bpm']}  beats {len(times)}  downbeats {len(down)}  first downbeat {down[0] if len(down) else None}s",
          file=sys.stderr)

if __name__ == "__main__":
    main()
