"""MemPolygraph pitch scenes — kinetic-technical, dark bg, 720p (upscaled in assembly).
Reads ~/mpv-build/durations.json; each scene lasts audio + 1s headroom.
Render: manim -qm pitch.py Hook Problem Product Proof Vision
"""
import json
import os
from manim import *

DUR = json.load(open(os.path.expanduser("~/mpv-build/durations.json")))
config.pixel_width = 1280
config.pixel_height = 720
config.background_color = "#0b0e14"

ACCENT = "#5eead4"
WARN = "#f87171"
DIM = "#94a3b8"


def dur(key, pad=1.0):
    return DUR[key] + pad


class Hook(Scene):
    def construct(self):
        t1 = Text("Your agent remembers.", font_size=54).shift(UP * 0.5)
        t2 = Text("Prove it.", font_size=54, color=ACCENT).next_to(t1, DOWN)
        self.play(Write(t1), run_time=2)
        self.play(Write(t2), run_time=1.5)
        self.wait(dur("pitch-S1HOOK") - 3.5 + 1)


class Problem(Scene):
    def construct(self):
        title = Text("Trust without proof is a bug.", font_size=40, color=WARN)
        self.play(Write(title), run_time=1.5)
        wallet = Text("wallet: 1.250 USDC", font_size=42, font="monospace").shift(DOWN * 0.3)
        drain = Text("wallet: 0.000 USDC", font_size=42, font="monospace", color=WARN).shift(DOWN * 0.3)
        note = Text("one bad recall", font_size=28, color=DIM).shift(DOWN * 1.5)
        self.play(FadeIn(wallet), run_time=1)
        self.play(Transform(wallet, drain), run_time=2)
        self.play(FadeIn(note), run_time=1)
        self.wait(max(0.5, dur("pitch-S2PROBLEM") - 5.5 + 1))


class Product(Scene):
    def construct(self):
        boxes = VGroup(*[
            VGroup(
                RoundedRectangle(corner_radius=0.15, width=2.2, height=1.1, color=ACCENT),
                Text(lbl, font_size=20))
            for lbl in ["memories", "black-box", "12 tests", "score+fp"]
        ]).arrange(RIGHT, buff=0.5).scale(0.95)
        arrows = VGroup(*[Arrow(LEFT, RIGHT, color=DIM, stroke_width=4)
                           for _ in range(3)])
        for i, a in enumerate(arrows):
            a.next_to(boxes[i], RIGHT, buff=0.05).shift(RIGHT * 0.2)
        title = Text("MemPolygraph", font_size=44, color=ACCENT).to_edge(UP)
        self.play(Write(title), run_time=1)
        for i, b in enumerate(boxes):
            self.play(FadeIn(b), run_time=0.8)
            if i < 3:
                self.play(GrowArrow(arrows[i]), run_time=0.5)
        self.wait(max(0.5, dur("pitch-S3PRODUCT") - 6 + 1))


class Proof(Scene):
    def construct(self):
        title = Text("71.87  →  90.0 Elder", font_size=48).to_edge(UP)
        bar = Rectangle(width=8, height=0.6, color=DIM).shift(DOWN * 0.5)
        fill = Rectangle(width=8, height=0.6, color=ACCENT, fill_opacity=1).align_to(bar, LEFT)
        fill.stretch_to_fit_width(8 * 0.72)
        line1 = Text("recall@5 1.0   abstain 4/4   adversarial clean",
                     font_size=26, font="monospace", color=DIM).shift(DOWN * 1.8)
        line2 = Text("+5 confirmed   -5 refuted", font_size=26, font="monospace",
                     color=ACCENT).shift(DOWN * 2.6)
        self.play(Write(title), run_time=1.2)
        self.play(FadeIn(bar), run_time=0.5)
        self.play(GrowFromEdge(fill, LEFT), run_time=2)
        self.play(Write(line1), run_time=1.2)
        self.play(Write(line2), run_time=1.2)
        self.wait(max(0.5, dur("pitch-S4PROOF") - 6.1 + 1))


class Vision(Scene):
    def construct(self):
        t1 = Text("SSL for agent commerce.", font_size=52, color=ACCENT)
        t2 = Text("Narrated by Synapse, autonomous agent.", font_size=28, color=DIM).shift(DOWN * 1)
        t3 = Text("Human founder: Marco Tessari.", font_size=28, color=DIM).shift(DOWN * 1.8)
        t4 = Text("Prove what your agent really remembers.", font_size=30).shift(DOWN * 2.7)
        self.play(Write(t1), run_time=1.8)
        self.play(FadeIn(t2), run_time=1)
        self.play(FadeIn(t3), run_time=1)
        self.play(Write(t4), run_time=1.5)
        self.wait(max(0.5, dur("pitch-S5VISIONTEAM") - 5.3 + 1))
