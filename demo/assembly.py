#!/usr/bin/env python3
"""Assemble pitch video: manim scenes (720p) + per-scene voiceover + burned subs -> 1080p mp4.
All work on Linux fs (BUILD). Run: MPV_BUILD=~/mpv-build python3 assembly.py
"""
import json
import os
import re
import shutil
import subprocess
import sys

REPO = "/mnt/e/skill-agent-v34/workspace/workflow/mempolygraph/demo"
BUILD = os.environ.get("MPV_BUILD", os.path.expanduser("~/mpv-build"))
os.makedirs(BUILD, exist_ok=True)

SCENES = ["Hook", "Problem", "Product", "Proof", "Vision"]
ASEC = ["pitch-S1HOOK", "pitch-S2PROBLEM", "pitch-S3PRODUCT", "pitch-S4PROOF", "pitch-S5VISIONTEAM"]
VOTEXT = "voiceover_pitch.txt"
OUTNAME = "pitch"
MODULE = "pitch"
if os.environ.get("VIDEO") == "demo":
    SCENES = ["D1", "D2", "D3", "D4", "D5"]
    ASEC = ["demo-D1SETUP", "demo-D2HARNESS", "demo-D3PASSPORT", "demo-D4LIVEENGINE", "demo-D5CLOSE"]
    VOTEXT = "voiceover_demo.txt"
    OUTNAME = "demo"
    MODULE = "demo"


def run(*args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL", args[0], r.stderr[-2000:])
        sys.exit(1)
    return r


def probe(path):
    r = run("ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", path)
    return float(r.stdout.strip())


# 1. stage assets onto Linux fs
for s in SCENES:
    shutil.copy(f"{REPO}/media/videos/{MODULE}/720p30/{s}.mp4", f"{BUILD}/{s}.mp4")
# audio files live in MPV_OUT/audio from tts.py run
AUDDIR = os.path.join(BUILD, "audio")
mp3list = []
base_idx = 0 if OUTNAME == "pitch" else 5
for i, key in enumerate(ASEC):
    src = os.path.join(AUDDIR, f"{base_idx+i:02d}-{key}.mp3")
    assert os.path.exists(src), f"missing {src}"
    mp3list.append(src)

# 2. per-scene video durations + pad audio with silence to match
seg_v, seg_a = [], []
for i, s in enumerate(SCENES):
    v = probe(f"{BUILD}/{s}.mp4")
    a = probe(mp3list[i])
    seg_v.append(v)
    seg_a.append(a)
    run("ffmpeg", "-y", "-v", "error", "-i", mp3list[i], "-af",
        f"apad=whole_dur={v:.3f}", "-c:a", "aac", "-ar", "44100",
        f"{BUILD}/a{i}.m4a")
    print(f"{s}: video={v:.2f}s audio={a:.2f}s pad={v-a:.2f}s")

# 3. concat video (scale 1080p) + concat audio
with open(f"{BUILD}/vlist.txt", "w") as f:
    for s in SCENES:
        f.write(f"file '{BUILD}/{s}.mp4'\n")
with open(f"{BUILD}/alist.txt", "w") as f:
    for i in range(len(SCENES)):
        f.write(f"file '{BUILD}/a{i}.m4a'\n")
run("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{BUILD}/vlist.txt",
    "-vf", "scale=1920:1080,fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "20",
    "-preset", "medium", f"{BUILD}/{OUTNAME}_video.mp4")
run("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", f"{BUILD}/alist.txt",
    "-c:a", "aac", "-ar", "44100", f"{BUILD}/{OUTNAME}_audio.m4a")

# 4. subtitles synced to VIDEO timeline (sentence weights spread over each scene length)
with open(f"{REPO}/{VOTEXT}", encoding="utf-8") as f:
    raw = f.read()
texts = []
for block in re.split(r"## \S+ ", raw)[1:]:
    body = " ".join(l.strip() for l in block.splitlines()
                    if l.strip() and not l.strip().startswith("[") and not l.strip().startswith("#"))
    texts.append(body)
assert len(texts) == 5, len(texts)


def ts(x):
    h, r = divmod(x, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


cues, t0, n = [], 0.0, 0
for i, body in enumerate(texts):
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
    w = [max(1, len(s.split())) for s in sents]
    tot = sum(w)
    for s, ww in zip(sents, w):
        d = seg_v[i] * ww / tot
        n += 1
        cues.append((n, t0, t0 + d, s))
        t0 += d
with open(f"{BUILD}/{OUTNAME}.srt", "w", encoding="utf-8") as f:
    for n, a, b, s in cues:
        f.write(f"{n}\n{ts(a)} --> {ts(b)}\n{s}\n\n")

# 5. mux + burn subs + faststart
run("ffmpeg", "-y", "-v", "error", "-i", f"{BUILD}/{OUTNAME}_video.mp4", "-i", f"{BUILD}/{OUTNAME}_audio.m4a",
    "-vf", f"subtitles={BUILD}/{OUTNAME}.srt:force_style='FontSize=22,PrimaryColour=&HFFFFFF&,OutlineColour=&H80000000&,BorderStyle=1,Outline=2'",
    "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-c:a", "aac",
    "-movflags", "+faststart", "-shortest", f"{BUILD}/{OUTNAME}_final.mp4")

# 6. QA
d = probe(f"{BUILD}/{OUTNAME}_final.mp4")
r = run("ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name", "-of", "csv",
        f"{BUILD}/{OUTNAME}_final.mp4")
size = os.path.getsize(f"{BUILD}/{OUTNAME}_final.mp4")
print(f"FINAL duration={d:.1f}s size={size/1e6:.1f}MB {r.stdout.strip()}")
assert d > 60, "too short?"
assert size < 256e6, "too big for portal?"
print(OUTNAME + " OK")
