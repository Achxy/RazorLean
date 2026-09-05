# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

from ..shared import *  # noqa: F401,F403


class OpeningProof(ProofScene):
    TARGET = 44.0

    def construct(self):
        title = self.title("Alice sells Bob a tiny add-on for ₹2.01.", 47)
        alice = stick_person("ALICE", PURPLE, "happy", 0.92).move_to([-4.35, -0.78, 0])
        bob = stick_person("BOB", BLUE, "happy", 0.92).move_to([4.35, -0.78, 0])
        alice_words = speech_bubble("Just ₹2.01.", PURPLE, size=34, max_width=3.2)
        alice_words.move_to([-3.35, 1.20, 0])
        bob_words = speech_bubble("Buy.", BLUE, size=34, max_width=2.5)
        bob_words.move_to([3.35, 1.20, 0])
        ticket = RoundedRectangle(width=1.55, height=0.90, corner_radius=0.10, color=YELLOW, stroke_width=2.5)
        amount = display("₹2.01", 31, YELLOW, "BOLD").move_to(ticket)
        payment = VGroup(ticket, amount).move_to([2.55, -0.55, 0])
        # Keep direction and payload on separate visual lanes.  The previous
        # arrow shared the ticket's y-range, so its tip visibly pierced the
        # card after the ticket reached Alice.
        path = Arrow([1.95, 0.28, 0], [-1.95, 0.28, 0], buff=0.0, color=GREEN, stroke_width=3)
        payment_at_alice = payment.copy().move_to([-2.55, -0.55, 0])
        payment_sweep = Rectangle(
            width=5.10 + payment.width,
            height=payment.height,
            stroke_opacity=0,
        ).move_to([0, -0.55, 0])
        paid = check(GREEN, 1.0).move_to([0, -0.55, 0])
        # This tests the complete translation envelope, not only its endpoints.
        assert_disjoint("opening-transfer-sweep", path, payment_sweep, gap=0.12)
        assert_disjoint("opening-transfer-start", path, payment, paid, gap=0.12)
        assert_disjoint("opening-transfer-finish", path, payment_at_alice, paid, gap=0.12)
        assert_disjoint("opening-story", title, alice_words, bob_words, Group(alice, path, payment, bob), gap=0.12)

        self.play(Write(title), run_time=0.9)
        self.play(LaggedStart(FadeIn(alice), FadeIn(bob), lag_ratio=0.25), run_time=0.9)
        self.play(FadeIn(alice_words, shift=UP * 0.06), run_time=0.7)
        self.wait(0.8)
        self.play(FadeIn(bob_words, shift=UP * 0.06), run_time=0.6)
        self.play(FadeIn(payment), GrowArrow(path), run_time=0.55)
        self.play(payment.animate.move_to([-2.55, -0.55, 0]), run_time=1.15, rate_func=EASE)
        self.play(Create(paid), run_time=0.55)
        self.wait(6.0)
        self.clear(title, alice, bob, alice_words, bob_words, path, payment, paid)

        dashboard_title = self.title("The integration call succeeds. The order does not mean ₹2.01.", 42)
        dashboard = source_image("razorpay-undercharge-dashboard-unredacted.png", 12.35, 3.15, BLUE)
        dashboard.move_to([0, 0.25, 0])
        verdict = VGroup(
            display("Alice asked", 35, WHITE),
            display("₹2.01", 46, YELLOW, "BOLD"),
            display("Razorpay received", 35, WHITE),
            display("₹2.00", 46, RED, "BOLD"),
        ).arrange(RIGHT, buff=0.30).move_to([0, -2.13, 0])
        assert_disjoint("opening-dashboard-verdict", *verdict, gap=0.12)
        quiet = display("No error. No warning.", 39, GREEN).move_to([0, -2.92, 0])
        assert_disjoint("opening-dashboard", dashboard_title, dashboard, verdict, quiet, gap=0.13)
        self.play(Write(dashboard_title), run_time=0.85)
        self.play(FadeIn(dashboard, shift=UP * 0.06), run_time=1.0)
        self.wait(1.2)
        self.play(LaggedStart(*[FadeIn(part, shift=UP * 0.05) for part in verdict], lag_ratio=0.12), run_time=1.0)
        self.play(Write(quiet), run_time=0.65)
        self.wait(7.0)
        self.clear(dashboard_title, dashboard, verdict, quiet)

        cause_title = self.title("Only now do we open the generated code.", 45)
        source = source_image("github-generated-money-clip.png", 9.7, 2.55, BLUE)
        source.move_to([0, 0.75, 0])
        expression = code("int(2.01 × 100)", 37, YELLOW, "BOLD").move_to([0, -1.15, 0])
        represented = code("200.99999999999997", 35, GOLD, "BOLD").move_to([0, -1.88, 0])
        result = VGroup(display("→", 37, GREY), code("200", 42, RED, "BOLD"), small_label("SUBUNITS", RED))
        result.arrange(RIGHT, buff=0.24).move_to([0, -2.68, 0])
        assert_disjoint("opening-result-components", *result, gap=0.10)
        assert_disjoint("opening-cause", cause_title, source, expression, represented, result, gap=0.11)
        self.play(Write(cause_title), FadeIn(source, shift=UP * 0.06), run_time=1.0)
        self.wait(0.8)
        self.play(Write(expression), run_time=0.75)
        self.play(FadeIn(represented, shift=DOWN * 0.05), run_time=0.8)
        self.play(FadeIn(result, shift=DOWN * 0.05), run_time=0.75)
        self.play(ShowPassingFlash(Underline(result[1], color=RED, buff=0.08), time_width=0.65), run_time=0.7)
        self.wait(6.0)
        self.clear(cause_title, source, expression, represented, result)

        alice = stick_person("ALICE", PURPLE, "sad", 1.0).move_to([-3.6, -0.45, 0])
        loss = display("1 paisa", 70, RED, "BOLD").move_to([1.65, 0.50, 0])
        line1 = display("Nothing crashed.", 45, GREEN).move_to([1.65, -0.52, 0])
        line2 = display("Alice's order was silently changed.", 42, WHITE).move_to([1.65, -1.38, 0])
        fit(line2, 8.2)
        assert_disjoint("opening-human-cost", alice, Group(loss, line1, line2), gap=0.55)
        self.play(FadeIn(alice), Write(loss), run_time=0.85)
        self.play(Write(line1), run_time=0.65)
        self.play(Write(line2), run_time=0.70)
        self.finish()
