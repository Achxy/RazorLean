# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

from ..shared import *  # noqa: F401,F403


class ProviderEvidence(ProofScene):
    TARGET = 27.0

    def construct(self):
        title = self.title("Run both paths. Read the provider's own dashboard.", 44)
        wrong = source_image("razorpay-undercharge-dashboard-unredacted.png", 6.15, 2.65, RED)
        right = source_image("razorpay-exact-dashboard-unredacted.png", 6.15, 2.65, GREEN)
        wrong.move_to([-3.25, 0.35, 0])
        right.move_to([3.25, 0.35, 0])
        wrong_label = VGroup(display("Alice asked ₹2.01", 31, WHITE), display("order: ₹2.00", 38, RED, "BOLD"))
        right_label = VGroup(display("Alice asked ₹2.01", 31, WHITE), display("order: ₹2.01", 38, GREEN, "BOLD"))
        wrong_label.arrange(DOWN, buff=0.18).move_to([-3.25, -1.75, 0])
        right_label.arrange(DOWN, buff=0.18).move_to([3.25, -1.75, 0])
        verdict = display("Same provider. Different boundary.", 39, YELLOW).move_to([0, -2.87, 0])
        assert_disjoint("evidence-comparison", title, wrong, right, wrong_label, right_label, verdict, gap=0.13)
        self.play(Write(title), run_time=0.75)
        self.play(FadeIn(wrong, shift=RIGHT * 0.05), FadeIn(wrong_label), run_time=0.95)
        self.play(FadeIn(right, shift=LEFT * 0.05), FadeIn(right_label), run_time=0.95)
        self.wait(1.5)
        self.play(Write(verdict), run_time=0.65)
        self.wait(5.0)
        self.clear(title, wrong, right, wrong_label, right_label, verdict)

        title2 = self.title("Then repeat the experiment across currencies.", 45)
        currencies = source_image("razorpay-orders-currency-pairs.png", 11.8, 4.50, BLUE)
        currencies.move_to([0, -0.05, 0])
        caption = display("Exact and broken orders coexist on the real surface.", 36, WHITE)
        caption.move_to([0, -2.88, 0])
        assert_disjoint("evidence-currencies", title2, currencies, caption, gap=0.13)
        self.play(Write(title2), FadeIn(currencies, shift=UP * 0.05), run_time=1.0)
        self.wait(2.2)
        self.play(Write(caption), run_time=0.65)
        self.wait(5.0)
        self.clear(title2, currencies, caption)

        title3 = self.title("Captured and refunded states remain independently visible.", 42)
        captured = source_image("razorpay-captured-payment-status.png", 5.7, 1.05, GREEN)
        refunded = source_image("razorpay-refunded-payment-status.png", 5.7, 1.05, BLUE)
        captured.move_to([-3.15, 0.75, 0])
        refunded.move_to([3.15, 0.75, 0])
        alice = stick_person("ALICE", PURPLE, "happy", 0.73).move_to([-3.15, -1.45, 0])
        bob = stick_person("BOB", BLUE, "happy", 0.73).move_to([3.15, -1.45, 0])
        result = display("Every claim can be replayed against Razorpay.", 40, GREEN).move_to([0, -2.92, 0])
        assert_disjoint("evidence-states", title3, captured, refunded, Group(alice, bob), result, gap=0.12)
        self.play(Write(title3), FadeIn(captured), FadeIn(refunded), run_time=0.9)
        self.play(FadeIn(alice), FadeIn(bob), run_time=0.75)
        self.play(Write(result), run_time=0.75)
        self.finish()
