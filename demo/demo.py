"""Demo scenes — terminal-style, real captured outputs, 720p (upscaled in assembly).
Reads ~/mpv-build/durations.json (demo-D* keys).
Render: manim -qm demo.py D1 D2 D3 D4 D5
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


def term(lines, fs=22):
    g = VGroup(*[Text(l, font_size=fs, font="monospace",
                       color=GREEN if l.startswith(("$", "{", "}")) else DIM)
                 for l in lines]).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
    g.scale(0.85)
    # keep block top-anchored and clear of the subtitle zone (bottom 25%)
    g.to_edge(LEFT, buff=0.8).to_edge(UP, buff=0.9)
    return g


def tagline(text):
    """Bottom tag, parked at y=-1.4 — above the subtitle zone."""
    return Text(text, font_size=26, color=ACCENT).move_to(DOWN * 1.4)


class D1(Scene):
    def construct(self):
        scr = term(["$ docker build -t mempolygraph .",
                    " => [internal] load build definition",
                    " => [4/4] RUN python -m src.eval_harness",
                    " => naming to docker.io/library/mempolygraph",
                    "$ docker run --rm mempolygraph"])
        for i, line in enumerate(scr):
            self.play(FadeIn(line, shift=UP * 0.2), run_time=0.7)
        self.wait(max(0.5, dur("demo-D1SETUP") - len(scr) * 0.7))


class D2(Scene):
    def construct(self):
        scr = term(['"pass": true,',
                    '"recall_at_3": 0.875,',
                    '"abstain_acc": 1.0,',
                    '"adv_clean": 1.0,',
                    '"deterministic": true'])
        for line in scr:
            self.play(FadeIn(line, shift=UP * 0.2), run_time=0.7)
        tag = tagline("anti-invention gate: 2 refused, 2 deflected")
        self.play(Write(tag), run_time=1.2)
        self.wait(max(0.5, dur("demo-D2HARNESS") - len(scr) * 0.7 - 1.2))


class D3(Scene):
    def construct(self):
        scr = term(['"accuracy": 0.925,',
                    '"gate_pass": true,',
                    '"fingerprint": "86a0717354c652c...",'])
        for line in scr:
            self.play(FadeIn(line, shift=UP * 0.2), run_time=0.9)
        tag = tagline("recompute the SHA yourself")
        self.play(Write(tag), run_time=1.2)
        self.wait(max(0.5, dur("demo-D3PASSPORT") - 3 * 0.9 - 1.2))


class D4(Scene):
    def construct(self):
        t = Text("same harness, real production memory", font_size=34).shift(UP * 2.2)
        scr = term(['"agent": "synapse-k3",',
                    '"accuracy": 0.925,',
                    '"gate_pass": true'])
        lock = tagline("engine never leaves this machine")
        self.play(Write(t), run_time=1.2)
        for line in scr:
            self.play(FadeIn(line, shift=UP * 0.2), run_time=0.7)
        self.play(Write(lock), run_time=1.2)
        self.wait(max(0.5, dur("demo-D4LIVEENGINE") - 1.2 - 3 * 0.7 - 1.2))


class D5(Scene):
    def construct(self):
        t1 = Text("Methodology, fixtures and code in the repo.", font_size=34).shift(UP * 1.4)
        t2 = Text("Verify everything yourself.", font_size=34, color=ACCENT).shift(DOWN * 0.2)
        t3 = Text("MemPolygraph.", font_size=40).shift(DOWN * 1.5)
        self.play(Write(t1), run_time=1.4)
        self.play(Write(t2), run_time=1.2)
        self.play(FadeIn(t3), run_time=1)
        self.wait(max(0.5, dur("demo-D5CLOSE") - 3.6))
