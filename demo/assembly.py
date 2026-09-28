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
    ASEC = [["demo-D1SETUP"], ["demo-D2HARNESS"], ["demo-D3PASSPORT"], ["demo-D4LIVEENGINE"], ["demo-D5CLOSE"]]
    VOTEXT = "voiceover_demo.txt"
    OUTNAME = "demo"
    MODULE = "demo"
else:
    ASEC = [[k] for k in ASEC]
if os.environ.get("VIDEO") == "weekly":
    SCENES = ["W2"]
    ASEC = [["weekly-W2BUILT", "weekly-W2LEARNED", "weekly-W2NEXT"]]
    VOTEXT = "voiceover_weekly_w2.txt"
    OUTNAME = "weekly"
    MODULE = "weekly"


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
# audio files live in MPV_OUT/audio from tts.py run: NN-<key>.mp3
AUDDIR = os.path.join(BUILD, "audio")
namemap = {}
for f in os.listdir(AUDDIR):
    if f.endswith(".mp3") and "-" in f:
        namemap[f.split("-", 1)[1][:-4]] = os.path.join(AUDDIR, f)
mp3list = []
for i, keys in enumerate(ASEC):
    parts = []
    for key in keys:
        assert key in namemap, f"missing audio for {key}"
        parts.append(namemap[key])
    if len(parts) == 1:
        mp3list.append(parts[0])
    else:  # concat multiple sections into one scene track
        lst = f"{BUILD}/au{i}.txt"
        with open(lst, "w") as f:
            for p in parts:
                f.write(f"file '{p}'\n")
        out = f"{BUILD}/au{i}.mp3"
        run("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
            "-i", lst, "-c:a", "libmp3lame", out)
        mp3list.append(out)

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
# ASEC groups audio sections per scene: [(scene0: [k..]), ...] — same order as SCENES
with open(f"{REPO}/{VOTEXT}", encoding="utf-8") as f:
    raw = f.read()
bodies = []
for block in re.split(r"## \S+ ", raw)[1:]:
    body = " ".join(l.strip() for l in block.splitlines()
                    if l.strip() and not l.strip().startswith("[") and not l.strip().startswith("#"))
    bodies.append(body)
flat_keys, flat_bodies = [], []
for keys in ASEC:
    for k in keys:
        flat_keys.append(k)
assert len(bodies) == len(flat_keys), (len(bodies), len(flat_keys))
key2body = dict(zip(flat_keys, bodies))
texts = [[key2body[k] for k in keys] for keys in ASEC]
assert len(texts) == len(SCENES)


def ts(x):
    h, r = divmod(x, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


def wrap(s, width=42):
    """Split sentence into short lines so subs never cover the scene."""
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + 1 + len(w) > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


cues, t0, n = [], 0.0, 0
for i, bodies in enumerate(texts):  # bodies = audio sections of scene i
    for body in bodies:
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
        w = [max(1, len(s.split())) for s in sents]
        tot = sum(w)
        share = seg_v[i] / max(1, len(bodies))
        for s, ww in zip(sents, w):
            d = share * ww / tot
            for line in wrap(s):
                dd = d / max(1, len(wrap(s)))
                n += 1
                cues.append((n, t0, t0 + dd, line))
                t0 += dd
with open(f"{BUILD}/{OUTNAME}.srt", "w", encoding="utf-8") as f:
    for n, a, b, s in cues:
        f.write(f"{n}\n{ts(a)} --> {ts(b)}\n{s}\n\n")

# 5. mux + burn subs + faststart
run("ffmpeg", "-y", "-v", "error", "-i", f"{BUILD}/{OUTNAME}_video.mp4", "-i", f"{BUILD}/{OUTNAME}_audio.m4a",
    "-vf", f"subtitles={BUILD}/{OUTNAME}.srt:force_style='FontSize=20,PrimaryColour=&HFFFFFF&,OutlineColour=&H80000000&,BackColour=&H99000000&,BorderStyle=3,Outline=1,Shadow=0,MarginV=28,Alignment=2'",
    "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-c:a", "aac",
    "-movflags", "+faststart", "-shortest", f"{BUILD}/{OUTNAME}_final.mp4")

# 6. QA
d = probe(f"{BUILD}/{OUTNAME}_final.mp4")
r = run("ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name", "-of", "csv",
        f"{BUILD}/{OUTNAME}_final.mp4")
size = os.path.getsize(f"{BUILD}/{OUTNAME}_final.mp4")
print(f"FINAL duration={d:.1f}s size={size/1e6:.1f}MB {r.stdout.strip()}")
assert d > 45, "too short?"
assert size < 256e6, "too big for portal?"
# subtitle hygiene: every cue line short, cues cover the timeline
longest, ncues, t_end = 0, 0, 0.0
with open(f"{BUILD}/{OUTNAME}.srt", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.isdigit() or "-->" in line:
            if "-->" in line:
                t_end = float(line.split("-->")[1].strip().split(":")[-1].replace(",", "."))
                mm = int(line.split(":")[1])
                t_end += mm * 60
            continue
        ncues += 1
        longest = max(longest, len(line))
print(f"SUBS cues={ncues} longest_line={longest} coverage_end={t_end:.1f}s")
assert longest <= 44, "subtitle line too long, will cover scene"
assert ncues >= 8, "too few cues?"
assert t_end > d * 0.8, "subs do not cover video"
print(OUTNAME + " OK")
