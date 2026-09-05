# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

from ..shared import *  # noqa: F401,F403


class LostCoordinate(ProofScene):
    TARGET = 38.0

    def construct(self):
        title = self.title("Bob has a green check. Alice still has a problem.", 45)
        alice = stick_person("ALICE", PURPLE, "sad", 0.95).move_to([-4.15, -0.70, 0])
        bob = stick_person("BOB", BLUE, "happy", 0.95).move_to([4.15, -0.70, 0])
        bob_words = speech_bubble("I paid the order you sent.", BLUE, size=30, max_width=4.3)
        bob_words.move_to([3.15, 1.20, 0])
        alice_words = speech_bubble("But was it the order I meant?", PURPLE, size=29, max_width=4.5)
        alice_words.move_to([-2.95, 1.20, 0])
        valid = VGroup(check(GREEN, 1.1), display("valid", 35, GREEN, "BOLD")).arrange(DOWN, buff=0.18)
        valid.move_to([0, -0.25, 0])
        assert_disjoint("signature-story", title, alice_words, bob_words, Group(alice, valid, bob), gap=0.10)
        self.play(Write(title), FadeIn(alice), FadeIn(bob), run_time=0.9)
        self.play(FadeIn(bob_words, shift=UP * 0.05), run_time=0.75)
        self.play(Create(valid[0]), FadeIn(valid[1]), run_time=0.65)
        self.wait(0.7)
        self.play(FadeIn(alice_words, shift=UP * 0.05), run_time=0.75)
        self.wait(6.0)
        self.clear(title, alice, bob, bob_words, alice_words, valid)

        title2 = self.title("The signature proves a payment belongs to an order.", 45)
        verify = source_image("github-verifier-clip.png", 10.8, 3.45, GREEN)
        verify.move_to([0, 0.45, 0])
        bound = VGroup(
            code("order_id", 34, BLUE, "BOLD"),
            display("+", 32, GREY),
            code("payment_id", 34, GREEN, "BOLD"),
        ).arrange(RIGHT, buff=0.34).move_to([0, -1.76, 0])
        assert_disjoint("signature-bound-components", *bound, gap=0.14)
        answer = display("That proof can be perfectly valid.", 40, GREEN).move_to([0, -2.63, 0])
        assert_disjoint("signature-code", title2, verify, bound, answer, gap=0.12)
        self.play(Write(title2), run_time=0.75)
        self.play(FadeIn(verify, shift=UP * 0.06), run_time=0.95)
        self.wait(0.8)
        self.play(FadeIn(bound), run_time=0.75)
        self.play(Write(answer), run_time=0.65)
        self.wait(5.5)
        self.clear(title2, verify, bound, answer)

        title3 = self.title("But Alice's meaning was larger than those two IDs.", 44)
        meaning = VGroup(
            code("ALICE", 28, PURPLE, "BOLD"),
            display("₹2.01", 42, YELLOW, "BOLD"),
            code("INR", 28, BLUE, "BOLD"),
            code("CART", 28, TEAL, "BOLD"),
            code("ORDER", 28, GREEN, "BOLD"),
            code("PAYMENT", 28, GREEN, "BOLD"),
        ).arrange(RIGHT, buff=0.44).move_to([0, 1.15, 0])
        fit(meaning, 11.8)
        assert_disjoint("meaning-components", *meaning, gap=0.13)
        brace = Brace(meaning, DOWN, color=GREY)
        projection = Arrow([0, 0.38, 0], [0, -0.48, 0], color=GREY, stroke_width=2.5)
        survivor = VGroup(meaning[4].copy(), meaning[5].copy()).arrange(RIGHT, buff=0.7).move_to([0, -1.05, 0])
        assert_disjoint("survivor-components", *survivor, gap=0.35)
        gone = VGroup(*[item.copy() for item in meaning[:4]]).arrange(RIGHT, buff=0.40).scale(0.82)
        gone.set_color(RED).move_to([0, -2.20, 0])
        assert_disjoint("gone-components", *gone, gap=0.09)
        crossed = Line(gone.get_left() + LEFT * 0.10, gone.get_right() + RIGHT * 0.10, color=RED, stroke_width=4)
        assert_disjoint("meaning-projection", title3, Group(meaning, brace), projection, survivor, Group(gone, crossed), gap=0.12)
        self.play(Write(title3), FadeIn(meaning), GrowFromCenter(brace), run_time=0.95)
        self.wait(0.65)
        self.play(GrowArrow(projection), FadeIn(survivor), run_time=0.85)
        self.play(FadeIn(gone), Create(crossed), run_time=0.85)
        self.wait(5.5)
        self.clear(title3, meaning, brace, projection, survivor, gone, crossed)

        bob = stick_person("BOB", BLUE, "neutral", 0.88).move_to([5.15, -0.62, 0])
        alice = stick_person("ALICE", PURPLE, "sad", 0.88).move_to([-5.15, -0.62, 0])
        center = VGroup(
            display("A valid payment", 48, GREEN),
            display("can settle the wrong promise.", 48, RED),
        ).arrange(DOWN, buff=0.28).move_to([0, 0.65, 0])
        fit(center, 7.2)
        assert_disjoint("signature-conclusion", alice, center, bob, gap=0.45)
        self.play(FadeIn(alice), FadeIn(bob), Write(center[0]), run_time=0.85)
        self.play(Write(center[1]), run_time=0.75)
        self.finish()
