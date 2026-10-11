#!/usr/bin/env python3
"""Build Weekly W4 — stile W3 (ffmpeg+gTTS, statico 1080p + subs burnati).
Run in WSL: ~/mpv-venv/bin/python /mnt/e/skill-agent-v34/workspace/workflow/mempolygraph/demo/build_w4.py
Non usa /tmp (volatile). Output: ~/mpv-build-w4/weekly_w4_final.mp4 + weekly_w4.srt
"""
import os
import re
import json
import subprocess
import sys

REPO = "/mnt/e/skill-agent-v34/workspace/workflow/mempolygraph/demo"
BUILD = os.environ.get("MPV_BUILD_W4", "/home/marco/mpv-build-w4")
AUDIO = os.path.join(BUILD, "audio")
os.makedirs(AUDIO, exist_ok=True)
os.makedirs(BUILD, exist_ok=True)

VOICEOVER = os.path.join(REPO, "voiceover_weekly_w4.txt")

# 1. parse 3 sezioni
sections = []
cur_title, cur_lines = None, []
with open(VOICEOVER, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line.startswith("## "):
            if cur_title:
                sections.append((cur_title, " ".join(cur_lines)))
            # "## W4-BUILT [0:00-0:22]" -> "weekly-W4BUILT"
            name = line[3:].split("[")[0].strip().replace("-", "")
            cur_title = "weekly-" + name
            cur_lines = []
        elif line and not line.startswith("#"):
            cur_lines.append(line)
if cur_title:
    sections.append((cur_title, " ".join(cur_lines)))

assert len(sections) == 3, f"attese 3 sezioni, trovate {len(sections)}: {[s[0] for s in sections]}"
print(f"sezioni: {[s[0] for s in sections]}")
for t, txt in sections:
    print(f"  {t}: {len(txt.split())} parole")

from gtts import gTTS
from mutagen.mp3 import MP3

durations = {}
mp3s = []
for i, (title, text) in enumerate(sections):
    mp3 = os.path.join(AUDIO, f"{i:02d}-{title}.mp3")
    if not os.path.exists(mp3):
        print(f"TTS {title} ...")
        gTTS(text=text, lang="en").save(mp3)
    else:
        print(f"TTS {title} riuso cache")
    dur = float(MP3(mp3).info.length)
    durations[title] = dur
    mp3s.append(mp3)
    print(f"  {title}: {dur:.2f}s")

with open(os.path.join(BUILD, "durations_w4.json"), "w") as f:
    json.dump(durations, f, indent=1)

# 2. timeline globale con pause 0.4s (come tts.py) + coda 1.0s
# subs wrappati a max 42 char come assembly.py (mai sotto y=-2.0)
def wrap(s, width=42):
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

GAP = 0.4
TAIL = 1.0
srt_cues = []
t = 0.0
for title, text in sections:
    dur = durations[title]
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    weights = [max(1, len(s.split())) for s in sents]
    total = sum(weights)
    for s, w in zip(sents, weights):
        d = dur * w / total
        lines = wrap(s)
        dd = d / max(1, len(lines))
        for line in lines:
            srt_cues.append((t, t + dd, line))
            t += dd
    t += GAP
total_audio = t - GAP + TAIL
print(f"durata audio totale + coda: {total_audio:.2f}s")

def ts(x):
    h, r = divmod(x, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"

srt_path = os.path.join(BUILD, "weekly_w4.srt")
with open(srt_path, "w", encoding="utf-8") as f:
    for n, (a, b, s) in enumerate(srt_cues, 1):
        f.write(f"{n}\n{ts(a)} --> {ts(b)}\n{s}\n\n")
print(f"SRT: {len(srt_cues)} cues -> {srt_path}")

# 3. audio concatenato con silenzi
def run(*args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL", args[0], r.stderr[-3000:])
        sys.exit(1)
    return r

# silenzio 0.4s + coda 1.0s
sil_path = os.path.join(BUILD, "sil04.mp3")
if not os.path.exists(sil_path):
    run("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-t", "0.4", "-c:a", "libmp3lame", sil_path)
tail_path = os.path.join(BUILD, "tail10.mp3")
if not os.path.exists(tail_path):
    run("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-t", "1.0", "-c:a", "libmp3lame", tail_path)

lst = os.path.join(BUILD, "aconcat.txt")
with open(lst, "w") as f:
    for i, p in enumerate(mp3s):
        f.write(f"file '{p}'\n")
        if i < len(mp3s) - 1:
            f.write(f"file '{sil_path}'\n")
    f.write(f"file '{tail_path}'\n")
audio_full = os.path.join(BUILD, "w4_audio.mp3")
run("ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
    "-i", lst, "-c:a", "libmp3lame", audio_full)

def probe(path):
    r = run("ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", path)
    return float(r.stdout.strip())

adur = probe(audio_full)
print(f"audio concatenato: {adur:.2f}s")
D = max(adur, 51.0)  # minimo 51s come W3, evita video troppo corto
print(f"durata video target: {D:.2f}s")

# 4. testi on-screen (plain ASCII, niente em-dash per drawtext)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
title_txt = "MemPolygraph - Week 4"
b1_txt = "BUILT: submission-ready, harness PASS, Docker verified"
b2_txt = "LEARNED: freeze repo, no-leak by design"
b3_txt = "NEXT: final submit before Oct 12"
for name, content in [("title.txt", title_txt), ("b1.txt", b1_txt),
                      ("b2.txt", b2_txt), ("b3.txt", b3_txt)]:
    with open(os.path.join(BUILD, name), "w", encoding="utf-8") as f:
        f.write(content)

# video base colore + testi centrati (zona alta, subs in basso 25%)
vf_base = (
    f"drawtext=fontfile={FONT}:textfile='{BUILD}/title.txt':"
    f"fontcolor=#5eead4:fontsize=72:x=(w-text_w)/2:y=140,"
    f"drawtext=fontfile={FONT_REG}:textfile='{BUILD}/b1.txt':"
    f"fontcolor=#4ade80:fontsize=34:x=(w-text_w)/2:y=380,"
    f"drawtext=fontfile={FONT_REG}:textfile='{BUILD}/b2.txt':"
    f"fontcolor=#94a3b8:fontsize=34:x=(w-text_w)/2:y=480,"
    f"drawtext=fontfile={FONT_REG}:textfile='{BUILD}/b3.txt':"
    f"fontcolor=#94a3b8:fontsize=34:x=(w-text_w)/2:y=580"
)
video_base = os.path.join(BUILD, "w4_video.mp4")
run("ffmpeg", "-y", "-v", "error", "-f", "lavfi",
    "-i", f"color=c=0x0b0e14:s=1920x1080:d={D:.3f}:r=30",
    "-vf", vf_base,
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "21", "-preset", "veryfast",
    video_base)
print(f"video base: {video_base} {D:.1f}s")

# 5. mux + burn subs + faststart
final_path = os.path.join(BUILD, "weekly_w4_final.mp4")
# subtitles filter: path senza ':' quindi sicuro
run("ffmpeg", "-y", "-v", "error",
    "-i", video_base, "-i", audio_full,
    "-vf", f"subtitles={srt_path}:force_style='FontSize=20,PrimaryColour=&HFFFFFF&,OutlineColour=&H80000000&,BackColour=&H99000000&,BorderStyle=3,Outline=1,Shadow=0,MarginV=28,Alignment=2'",
    "-c:v", "libx264", "-crf", "21", "-preset", "veryfast",
    "-c:a", "aac", "-ar", "44100",
    "-movflags", "+faststart", "-shortest", final_path)

# 6. QA
d = probe(final_path)
r = run("ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,codec_name", "-of", "csv",
        final_path)
size = os.path.getsize(final_path)
print(f"FINAL duration={d:.1f}s size={size/1e6:.1f}MB {r.stdout.strip()}")
assert 50 <= d <= 70, f"durata fuori range 50-70s: {d}"
assert size < 256e6, "troppo grande per portal"
longest, ncues = 0, 0
with open(srt_path, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.isdigit() or "-->" in line:
            continue
        ncues += 1
        longest = max(longest, len(line))
print(f"SUBS cues={ncues} longest_line={longest}")
assert longest <= 44, "riga sub troppo lunga, copre la scena"
assert ncues >= 8, "troppi pochi cues"
print("W4 OK -> " + final_path)
