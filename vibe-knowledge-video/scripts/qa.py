#!/usr/bin/env python3
"""Final-cut QA for a rendered video (needs only ffmpeg/ffprobe). Gates distilled from published vibe-knowledge skills.
Usage: python3 qa.py out/final.mp4 [--sheet out/contact_sheet.jpg] [--target-lufs -14]
Gates:
  specs      1920x1080, 30 fps, yuv420p, H.264
  color      bt709 tagged (primaries/transfer/matrix); untagged files can look ~2x darker on phones
  audio      AAC track present, length == video length (±0.15 s)
  loudness   integrated ≈ target LUFS (Douyin/Bilibili ≈ -14) ±1.5, true peak ≤ -1 dBTP
  brightness mean Y (YAVG) 30–60 and no 1-s window < 25 — near-black + thin glow lines risk "low quality" throttling
  freeze     no frozen stretch ≥ 2 s (unless intended)
Also writes a contact sheet (24 evenly spaced frames, 6x4) for a one-glance visual review.
"""
import argparse, json, re, subprocess, sys

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def probe(path):
    r = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path])
    if r.returncode:
        sys.exit(r.stderr)
    return json.loads(r.stdout)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("--sheet"); ap.add_argument("--target-lufs", type=float, default=-14.0)
    a = ap.parse_args()
    info = probe(a.video)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    au = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"].get("duration", 0))
    res = []  # (gate, ok, detail, fix)

    num, den = (v.get("r_frame_rate", "0/1").split("/") + ["1"])[:2]
    fps = float(num) / float(den or 1)
    ok = v["width"] == 1920 and v["height"] == 1080 and abs(fps - 30) < 0.01 and v.get("pix_fmt") == "yuv420p" and v.get("codec_name") == "h264"
    res.append(("specs", ok, f'{v["width"]}x{v["height"]} {fps:.2f}fps {v.get("pix_fmt")} {v.get("codec_name")}',
                "render with --codec=h264 and 30 fps; add --pixel-format=yuv420p"))

    tags = [v.get("color_primaries"), v.get("color_transfer"), v.get("color_space")]
    ok = all(t == "bt709" for t in tags)
    res.append(("color", ok, f"primaries/transfer/matrix = {tags}",
                "Remotion: --color-space=bt709 ; or retag: ffmpeg -i in.mp4 -c copy -bsf:v h264_metadata=colour_primaries=1:transfer_characteristics=1:matrix_coefficients=1 out.mp4"))

    if au is None:
        res.append(("audio", False, "no audio track", "mux the music/SFX in (a silent upload reads as unfinished)"))
    else:
        adur = float(au.get("duration", dur))
        vdur = float(v.get("duration", dur))
        ok = au.get("codec_name") == "aac" and abs(adur - vdur) <= 0.15
        res.append(("audio", ok, f'{au.get("codec_name")} audio {adur:.2f}s vs video {vdur:.2f}s',
                    "re-encode audio as AAC and trim/pad it to the video length"))
        r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-map", "0:a:0", "-af", "ebur128=peak=true", "-f", "null", "-"])
        I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
        tp = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r.stderr)
        if I:
            Iv, tpv = float(I[-1]), float(tp[-1]) if tp else 0.0
            ok = abs(Iv - a.target_lufs) <= 1.5 and tpv <= -1.0
            res.append(("loudness", ok, f"integrated {Iv:.1f} LUFS, true peak {tpv:.1f} dBTP (target {a.target_lufs} LUFS, ≤ -1 dBTP)",
                        f"ffmpeg -i in.mp4 -c:v copy -af loudnorm=I={a.target_lufs}:TP=-1.5:LRA=11 -c:a aac -b:a 192k out.mp4"))

    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-vf", "fps=2,signalstats,metadata=print:key=lavfi.signalstats.YAVG", "-f", "null", "-"])
    y = [float(x) for x in re.findall(r"YAVG=([\d.]+)", r.stderr)]
    if y:
        mean = sum(y) / len(y)
        wins = [sum(y[i:i + 2]) / len(y[i:i + 2]) for i in range(0, len(y), 2)]
        low = [i for i, w in enumerate(wins) if w < 25]
        ok = 30 <= mean <= 60 and not low
        span = f"; dark seconds: {low[:12]}{'…' if len(low) > 12 else ''}" if low else ""
        fix = ("too bright for the dark cinematic look: deepen the background / lower ambient glow" if mean > 60 else
               "lift the background (e.g. #0A0A1E→#121a2e radial), add a warm ambient pool behind the subject, or grade: -vf eq=brightness=0.04:gamma=1.15")
        res.append(("brightness", ok, f"mean YAVG {mean:.1f} (target 30–60), min 1-s window {min(wins):.1f}{span}", fix))

    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", a.video, "-vf", "freezedetect=n=0.003:d=2", "-map", "0:v:0", "-f", "null", "-"])
    fz = re.findall(r"freeze_start: ([\d.]+).*?freeze_duration: ([\d.]+)", r.stderr, re.S)
    res.append(("freeze", not fz, ", ".join(f"{float(s):.1f}s for {float(d):.1f}s" for s, d in fz) or "none ≥ 2 s",
                "a 2 s+ static stretch: add drift/breathing or cut it (intentional pauses are fine — just confirm)"))

    if a.sheet:
        n = 24
        rate = n / max(dur, 0.1)
        r = run(["ffmpeg", "-hide_banner", "-y", "-i", a.video, "-vf", f"fps={rate:.5f},scale=480:-1,tile=6x4:padding=6:margin=6", "-frames:v", "1", a.sheet])
        res.append(("contact sheet", r.returncode == 0, a.sheet if r.returncode == 0 else r.stderr[-200:], "check ffmpeg"))

    bad = 0
    for gate, ok, detail, fix in res:
        print(f"{'PASS' if ok else 'FAIL'}  {gate:<13} {detail}")
        if not ok:
            bad += 1
            print(f"      fix: {fix}")
    print(f"\n{len(res) - bad}/{len(res)} gates passed")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
