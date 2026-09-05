# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

from ..shared import *  # noqa: F401,F403


class BoundaryFailures(ProofScene):
    TARGET = 36.0

    def construct(self):
        title = self.title("Next, Bob pays on his phone.", 49)
        bob = stick_person("BOB", BLUE, "happy", 1.0).move_to([-3.75, -0.65, 0])
        phone = RoundedRectangle(width=1.55, height=2.65, corner_radius=0.18, color=BLUE, stroke_width=3)
        screen = Rectangle(width=1.25, height=1.90, color=DARK_GREY, stroke_width=1.5).move_to(phone).shift(UP * 0.15)
        phone_check = check(GREEN, 0.72).move_to(screen)
        device = VGroup(phone, screen, phone_check).move_to([1.00, -0.68, 0])
        bob_words = speech_bubble("Payment complete.", BLUE, size=31, max_width=3.6)
        bob_words.move_to([-2.95, 1.70, 0])
        provider = VGroup(check(GREEN, 0.95), display("CAPTURED", 42, GREEN, "BOLD"))
        provider.arrange(RIGHT, buff=0.30).move_to([4.00, 0.10, 0])
        assert_disjoint("mobile-story", title, bob_words, Group(bob, device, provider), gap=0.14)
        self.play(Write(title), FadeIn(bob), FadeIn(device), run_time=0.9)
        self.play(FadeIn(bob_words), Create(phone_check), run_time=0.75)
        self.play(Create(provider[0]), FadeIn(provider[1]), run_time=0.75)
        self.wait(5.5)
        self.clear(title, bob, device, bob_words, provider)

        title2 = self.title("The provider says Bob's payment is captured.", 45)
        status = source_image("razorpay-captured-payment-status.png", 6.4, 1.1, GREEN)
        ids = source_image("razorpay-captured-payment-ids.png", 8.6, 2.55, BLUE)
        status.move_to([0, 1.05, 0])
        ids.move_to([0, -0.75, 0])
        proof = display("Real payment. Real provider state.", 39, GREEN).move_to([0, -2.78, 0])
        assert_disjoint("captured-proof", title2, status, ids, proof, gap=0.14)
        self.play(Write(title2), run_time=0.75)
        self.play(FadeIn(status, shift=UP * 0.05), run_time=0.8)
        self.play(FadeIn(ids, shift=UP * 0.05), run_time=0.9)
        self.wait(1.2)
        self.play(Write(proof), run_time=0.65)
        self.wait(5.0)
        self.clear(title2, status, ids, proof)

        title3 = self.title("Now inspect the generated mobile client.", 46)
        mobile = source_image("github-mobile-empty-signature-clip.png", 10.3, 3.20, BLUE)
        mobile.move_to([0, 0.40, 0])
        empty = code('razorpay_signature: ""', 38, RED, "BOLD").move_to([0, -1.78, 0])
        app_state = VGroup(strike(RED, 0.85), display("PAYMENT FAILED", 40, RED, "BOLD"))
        app_state.arrange(RIGHT, buff=0.30).move_to([0, -2.68, 0])
        assert_disjoint("mobile-app-components", *app_state, gap=0.18)
        assert_disjoint("mobile-generated-code", title3, mobile, empty, app_state, gap=0.12)
        self.play(Write(title3), FadeIn(mobile, shift=UP * 0.05), run_time=1.0)
        self.wait(0.8)
        self.play(Write(empty), run_time=0.7)
        self.play(GrowFromCenter(app_state[0]), FadeIn(app_state[1]), run_time=0.75)
        self.wait(5.0)
        self.clear(title3, mobile, empty, app_state)

        bob = stick_person("BOB", BLUE, "neutral", 0.95).move_to([-4.1, -0.60, 0])
        alice = stick_person("ALICE", PURPLE, "sad", 0.95).move_to([4.1, -0.60, 0])
        bob_words = speech_bubble("My bank says paid.", BLUE, size=30, max_width=3.4).move_to([-3.2, 1.55, 0])
        alice_words = speech_bubble("My app says failed.", PURPLE, size=30, max_width=3.4).move_to([3.2, 1.55, 0])
        split = Line([0, 1.65, 0], [0, -1.80, 0], color=RED, stroke_width=2.2)
        note = display("Two independently observed halves of one failure shape.", 35, GOLD)
        fit(note, 11.2).move_to([0, -2.72, 0])
        assert_disjoint("mobile-ending-bubbles", bob_words, alice_words, gap=0.30)
        assert_disjoint("mobile-ending-left", bob_words, bob, note, gap=0.12)
        assert_disjoint("mobile-ending-right", alice_words, alice, note, gap=0.12)
        assert_in_frame("mobile-ending-divider", split)
        self.play(FadeIn(bob), FadeIn(alice), Create(split), run_time=0.8)
        self.play(FadeIn(bob_words), run_time=0.65)
        self.play(FadeIn(alice_words), run_time=0.65)
        self.play(Write(note), run_time=0.7)
        self.finish()
