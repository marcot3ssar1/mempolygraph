"""TTS per-section + durations. Reads demo/voiceover_pitch.txt + voiceover_demo.txt,
writes audio/*.mp3 + durations.json + subtitles.srt (sentence-proportional timing).
ove: gtts (pip) + ffprobe (ffmpeg).
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("MPV_OUT", HERE)  # build artifacts go to Linux fs if set
AUDIO = os.path.join(OUT, "audio")
os.makedirs(AUDIO, exist_ok=True)

SECTIONS = []
for fname in ("voiceover_pitch.txt", "voiceover_demo.txt", "voiceover_weekly_w2.txt"):
    prefix = {"voiceover_pitch.txt": "pitch", "voiceover_demo.txt": "demo",
              "voiceover_weekly_w2.txt": "weekly"}[fname]
    cur_title, cur_lines = None, []
    with open(os.path.join(HERE, fname), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("## "):
                if cur_title:
                    SECTIONS.append((cur_title, " ".join(cur_lines)))
                cur_title = prefix + "-" + re.sub(r"\W+", "", line[3:].split("[")[0].strip())
                cur_lines = []
            elif line and not line.startswith("#"):
                cur_lines.append(line)
    if cur_title:
        SECTIONS.append((cur_title, " ".join(cur_lines)))

from gtts import gTTS
from mutagen.mp3 import MP3

durations, srt_all, per_video = {}, [], {}
t_global, t_local, cur_video = 0.0, 0.0, None
for i, (title, text) in enumerate(SECTIONS):
    video = "pitch" if title.startswith("pitch-") else "demo"
    if video != cur_video:
        cur_video, t_local = video, 0.0
    mp3 = os.path.join(AUDIO, f"{i:02d}-{title}.mp3")
    if not os.path.exists(mp3):  # reuse cached audio, keep build reproducible
        gTTS(text=text, lang="en").save(mp3)
    dur = float(MP3(mp3).info.length)
    durations[title] = dur
    # sentence-proportional SRT cues, per-video local timeline
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    weights = [max(1, len(s.split())) for s in sents]
    total = sum(weights)
    for j, (s, w) in enumerate(zip(sents, weights)):
        s0, s1 = t_global, t_global + dur * w / total
        srt_all.append((len(srt_all) + 1, s0, s1, s))
        l0, l1 = t_local, t_local + dur * w / total
        per_video.setdefault(video, []).append((l0, l1, s))
        t_local += dur * w / total
    t_global += dur + 0.4  # breath gap
    t_local += 0.4

with open(os.path.join(OUT, "durations.json"), "w") as f:
    json.dump(durations, f, indent=1)


def ts(x):
    h, r = divmod(x, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


with open(os.path.join(OUT, "subtitles.srt"), "w", encoding="utf-8") as f:
    for n, a, b, s in srt_all:
        f.write(f"{n}\n{ts(a)} --> {ts(b)}\n{s}\n\n")
for video, cues in per_video.items():
    with open(os.path.join(OUT, f"{video}.srt"), "w", encoding="utf-8") as f:
        for n, (a, b, s) in enumerate(cues, 1):
            f.write(f"{n}\n{ts(a)} --> {ts(b)}\n{s}\n\n")
print(f"sections={len(SECTIONS)}")
print(json.dumps({k: round(v, 2) for k, v in durations.items()}, indent=1))
