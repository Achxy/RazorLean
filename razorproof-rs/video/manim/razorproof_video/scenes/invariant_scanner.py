# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

from ..shared import *  # noqa: F401,F403


class InvariantScanner(ProofScene):
    TARGET = 36.0

    def construct(self):
        title = self.title("Alice takes the same shop abroad.", 48)
        alice = stick_person("ALICE", PURPLE, "happy", 0.95).move_to([-4.25, -0.70, 0])
        bob_jpy = stick_person("BOB", BLUE, "neutral", 0.82).move_to([1.85, -0.70, 0])
        bob_kwd = stick_person("BOB", TEAL, "neutral", 0.82).move_to([4.75, -0.70, 0])
        jpy_words = speech_bubble("¥295", BLUE, size=34, max_width=2.3)
        jpy_words.move_to([1.55, 1.12, 0])
        kwd_words = speech_bubble("KWD 295.990", TEAL, size=30, max_width=3.0)
        kwd_words.move_to([4.25, 1.12, 0])
        alice_words = speech_bubble("Same checkout code.", PURPLE, size=30, max_width=3.5)
        alice_words.move_to([-3.30, 1.10, 0])
        assert_disjoint("currency-story", title, alice_words, jpy_words, kwd_words, Group(alice, bob_jpy, bob_kwd), gap=0.11)
        self.play(Write(title), FadeIn(alice), run_time=0.85)
        self.play(FadeIn(alice_words, shift=UP * 0.05), run_time=0.7)
        self.play(FadeIn(bob_jpy), FadeIn(jpy_words), run_time=0.75)
        self.play(FadeIn(bob_kwd), FadeIn(kwd_words), run_time=0.75)
        self.wait(5.5)
        self.clear(title, alice, bob_jpy, bob_kwd, alice_words, jpy_words, kwd_words)

        title2 = self.title("Here is what the real dashboard recorded.", 46)
        orders = source_image("razorpay-orders-currency-pairs.png", 12.15, 4.55, BLUE)
        orders.move_to([0, -0.05, 0])
        consequence = VGroup(
            display("JPY: 100× too large", 34, RED, "BOLD"),
            display("KWD: 10× too small", 34, RED, "BOLD"),
        ).arrange(RIGHT, buff=0.70).move_to([0, -2.92, 0])
        assert_disjoint("currency-consequence-components", *consequence, gap=0.35)
        assert_disjoint("currency-dashboard", title2, orders, consequence, gap=0.12)
        self.play(Write(title2), run_time=0.75)
        self.play(FadeIn(orders, shift=UP * 0.06), run_time=1.05)
        self.wait(1.8)
        self.play(FadeIn(consequence[0]), run_time=0.7)
        self.play(FadeIn(consequence[1]), run_time=0.7)
        self.wait(5.5)
        self.clear(title2, orders, consequence)

        title3 = self.title("The code assumed every currency has two decimal places.", 42)
        source = source_image("github-generated-money-clip.png", 9.5, 2.40, BLUE)
        source.move_to([0, 0.82, 0])
        fixed = code("amount × 100", 40, RED, "BOLD").move_to([0, -0.95, 0])
        rows = VGroup(
            VGroup(code("JPY", 27, BLUE, "BOLD"), code("× 1", 31, GREEN, "BOLD")),
            VGroup(code("INR", 27, BLUE, "BOLD"), code("× 100", 31, GREEN, "BOLD")),
            VGroup(code("KWD", 27, BLUE, "BOLD"), code("× 1000", 31, GREEN, "BOLD")),
        )
        for row in rows:
            row.arrange(RIGHT, buff=0.55)
            assert_disjoint("currency-rule-row", *row, gap=0.25)
        rows.arrange(RIGHT, buff=1.15).move_to([0, -2.08, 0])
        assert_disjoint("currency-rules", *rows, gap=0.55)
        invariant = display("Money needs a currency-aware type.", 40, YELLOW).move_to([0, -2.92, 0])
        assert_disjoint("currency-code", title3, source, fixed, rows, invariant, gap=0.12)
        self.play(Write(title3), FadeIn(source, shift=UP * 0.05), run_time=1.0)
        self.play(Write(fixed), run_time=0.7)
        self.play(ReplacementTransform(fixed.copy(), rows), run_time=1.1)
        self.play(Write(invariant), run_time=0.7)
        self.wait(5.5)
        self.clear(title3, source, fixed, rows, invariant)

        alice = stick_person("ALICE", PURPLE, "sad", 0.88).move_to([-5.15, -0.55, 0])
        result = VGroup(
            display("This is not cosmetic.", 46, WHITE),
            display("The same number buys a different thing.", 43, RED),
        ).arrange(DOWN, buff=0.35).move_to([1.15, 0.25, 0])
        fit(result, 7.7)
        assert_disjoint("currency-ending", alice, result, gap=0.48)
        self.play(FadeIn(alice), Write(result[0]), run_time=0.8)
        self.play(Write(result[1]), run_time=0.8)
        self.finish()
