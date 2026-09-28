"""Weekly W2 scene — same pro layout (nothing below y=-2.0).
Reads ~/mpv-build/durations.json (weekly-* keys).
Render: manim -qm weekly.py W2
"""
import json
import os
from manim import *

DUR = json.load(open(os.path.expanduser("~/mpv-build/durations.json")))
config.pixel_width = 1280
config.pixel_height = 720
config.background_color = "#0b0e14"

ACCENT = "#5eead4"
DIM = "#94a3b8"
GREEN = "#4ade80"


def dur(key):
    return DUR[key] + 1.0


class W2(Scene):
    def construct(self):
        title = Text("MemPolygraph — Week 2", font_size=44, color=ACCENT).shift(UP * 2.4)
        b1 = Text("BUILT: repo live, harness PASS, Docker verified",
                  font_size=28, font="monospace", color=GREEN).shift(UP * 0.9)
        b2 = Text("LEARNED: escrow fails on-chain; agent fixed own bug",
                  font_size=28, font="monospace", color=DIM).shift(DOWN * 0.1)
        b3 = Text("NEXT: live demo, packaging, submit Oct 11",
                  font_size=28, font="monospace", color=DIM).shift(DOWN * 1.1)
        self.play(Write(title), run_time=1.2)
        for b, k in ((b1, "weekly-W2BUILT"), (b2, "weekly-W2LEARNED"), (b3, "weekly-W2NEXT")):
            self.play(FadeIn(b, shift=UP * 0.2), run_time=1.0)
        total_anim = 1.2 + 3.0
        self.wait(max(0.5, dur("weekly-W2BUILT") + dur("weekly-W2LEARNED") + dur("weekly-W2NEXT") - total_anim))
