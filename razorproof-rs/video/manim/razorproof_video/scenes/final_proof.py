# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

from ..shared import *  # noqa: F401,F403


class FinalProof(ProofScene):
    TARGET = 15.0

    def construct(self):
        alice = stick_person("ALICE", PURPLE, "happy", 0.88).move_to([-5.10, -0.60, 0])
        bob = stick_person("BOB", BLUE, "happy", 0.88).move_to([5.10, -0.60, 0])
        promise = VGroup(
            display("Alice asked ₹2.01.", 43, YELLOW),
            display("Bob paid ₹2.01.", 43, GREEN),
            display("The purchase happened once.", 43, WHITE),
        ).arrange(DOWN, buff=0.30).move_to([0, 0.35, 0])
        fit(promise, 7.1)
        assert_disjoint("final-story", alice, promise, bob, gap=0.48)
        self.play(FadeIn(alice), FadeIn(bob), run_time=0.75)
        self.play(Write(promise[0]), run_time=0.65)
        self.play(Write(promise[1]), run_time=0.65)
        self.play(Write(promise[2]), run_time=0.65)
        self.wait(4.5)
        self.play(FadeOut(Group(alice, bob, promise), shift=UP * 0.05), run_time=0.55)

        logo = code("RAZORPROOF", 64, BLUE, "BOLD").move_to([0, 0.90, 0])
        rule = Line(LEFT * 2.7, RIGHT * 2.7, color=BLUE, stroke_width=2.2).move_to([0, 0.18, 0])
        tagline = display("The meaning Alice sets", 45, WHITE).move_to([0, -0.58, 0])
        tagline2 = display("is the meaning Bob pays.", 49, YELLOW).move_to([0, -1.38, 0])
        assert_disjoint("final-brand", logo, rule, tagline, tagline2, gap=0.14)
        self.play(Write(logo), Create(rule), run_time=0.8)
        self.play(Write(tagline), run_time=0.65)
        self.play(Write(tagline2), run_time=0.7)
        self.finish()
