# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

from ..shared import *  # noqa: F401,F403


class FailureChains(ProofScene):
    TARGET = 40.0

    def construct(self):
        title = self.title("Alice owes Bob a refund.", 51)
        alice = stick_person("ALICE", PURPLE, "neutral", 0.98).move_to([-4.15, -0.62, 0])
        bob = stick_person("BOB", BLUE, "neutral", 0.98).move_to([4.15, -0.62, 0])
        alice_words = speech_bubble("Send the refund once.", PURPLE, size=31, max_width=3.8)
        alice_words.move_to([-3.10, 1.62, 0])
        refund = VGroup(Circle(radius=0.48, color=YELLOW, stroke_width=3), display("₹", 38, YELLOW, "BOLD"))
        refund.move_to([0, -0.25, 0])
        # The refund is a foreground object, not a bead threaded by a line.
        # Two connector pieces leave a measured clear channel around it.
        path_in = Line([-3.35, -0.25, 0], [-0.66, -0.25, 0], color=GREEN, stroke_width=3)
        path_out = Arrow([0.66, -0.25, 0], [3.35, -0.25, 0], buff=0.0, color=GREEN, stroke_width=3)
        bob_words = speech_bubble("Got it.", BLUE, size=31, max_width=2.6).move_to([3.25, 1.62, 0])
        assert_disjoint("refund-story-bubbles", title, alice_words, bob_words, gap=0.12)
        assert_disjoint("refund-story-left", alice_words, alice, gap=0.12)
        assert_disjoint("refund-story-right", bob_words, bob, gap=0.12)
        assert_disjoint("refund-story-path-in", path_in, refund, gap=0.14)
        assert_disjoint("refund-story-path-out", refund, path_out, gap=0.14)
        self.play(Write(title), FadeIn(alice), FadeIn(bob), run_time=0.9)
        self.play(FadeIn(alice_words), run_time=0.65)
        self.play(Create(path_in), GrowArrow(path_out), FadeIn(refund), run_time=0.85)
        self.play(FadeIn(bob_words), run_time=0.65)
        self.wait(4.0)
        self.clear(title, alice, bob, alice_words, bob_words, refund, path_in, path_out)

        title2 = self.title("A malformed amount crossed the refund boundary.", 45)
        request = VGroup(
            small_label("REQUEST SENT", BLUE),
            code('"amount": 100.75', 39, YELLOW, "BOLD"),
        ).arrange(DOWN, buff=0.25).move_to([-3.25, 0.45, 0])
        response = VGroup(
            small_label("PROVIDER RESPONSE", GREEN),
            code('"amount": 100', 39, RED, "BOLD"),
            code('"status": "processed"', 29, GREEN, "BOLD"),
            code("rfnd_TXVx8F3EnIvxDV", 25, BLUE),
        ).arrange(DOWN, buff=0.23).move_to([3.10, 0.30, 0])
        transfer = Arrow(request.get_right(), response.get_left(), buff=0.25, color=GREY, stroke_width=2.5)
        changed = display("Accepted, but changed.", 43, RED).move_to([0, -2.13, 0])
        rule = display("A refund amount must be an integer subunit count.", 34, WHITE)
        fit(rule, 11.5).move_to([0, -2.93, 0])
        assert_disjoint("refund-request-response", title2, Group(request, transfer, response), changed, rule, gap=0.14)
        self.play(Write(title2), FadeIn(request), run_time=0.8)
        self.play(GrowArrow(transfer), FadeIn(response), run_time=1.0)
        self.wait(1.0)
        self.play(Write(changed), run_time=0.7)
        self.play(Write(rule), run_time=0.65)
        self.wait(3.8)
        self.clear(title2, request, response, transfer, changed, rule)

        title3 = self.title("Then Alice loses the response and retries.", 47)
        alice = stick_person("ALICE", PURPLE, "sad", 0.92).move_to([-4.45, -0.65, 0])
        first = VGroup(small_label("FIRST EFFECT", GREY), code("rfnd_TXVxKDFRx3nCqK", 25, GREEN, "BOLD"))
        second = VGroup(small_label("RETRY EFFECT", GREY), code("rfnd_TXVxMimmkZAB5W", 25, RED, "BOLD"))
        first.arrange(DOWN, buff=0.20).move_to([1.65, 0.78, 0])
        second.arrange(DOWN, buff=0.20).move_to([1.65, -0.55, 0])
        arrow1 = Arrow([-3.45, 0.10, 0], first.get_left(), buff=0.25, color=GREEN, stroke_width=2.5)
        arrow2 = CurvedArrow([-3.45, -0.30, 0], second.get_left(), angle=-0.35, color=RED, stroke_width=2.5)
        lost = strike(RED, 0.8).move_to([-0.65, 0.42, 0])
        total = display("Two provider effects for one human intention.", 37, RED)
        fit(total, 11.3).move_to([0, -2.48, 0])
        assert_disjoint("refund-retry", title3, Group(alice, arrow1, arrow2, lost, first, second), total, gap=0.13)
        self.play(Write(title3), FadeIn(alice), run_time=0.75)
        self.play(GrowArrow(arrow1), FadeIn(first), run_time=0.75)
        self.play(GrowFromCenter(lost), run_time=0.55)
        self.play(Create(arrow2), FadeIn(second), run_time=0.85)
        self.play(Write(total), run_time=0.7)
        self.wait(4.0)
        self.clear(title3, alice, arrow1, arrow2, lost, first, second, total)

        title4 = self.title("The dashboard shows the payment fully refunded.", 44)
        status = source_image("razorpay-refunded-payment-status.png", 6.5, 1.1, GREEN)
        ids = source_image("razorpay-refunded-payment-ids.png", 8.8, 2.55, BLUE)
        status.move_to([0, 1.08, 0])
        ids.move_to([0, -0.75, 0])
        meaning = display("The provider can report success while intent has already split.", 34, GOLD)
        fit(meaning, 11.4).move_to([0, -2.77, 0])
        assert_disjoint("refund-dashboard", title4, status, ids, meaning, gap=0.14)
        self.play(Write(title4), FadeIn(status), run_time=0.8)
        self.play(FadeIn(ids, shift=UP * 0.05), run_time=0.9)
        self.wait(1.2)
        self.play(Write(meaning), run_time=0.65)
        self.wait(3.8)
        self.clear(title4, status, ids, meaning)

        title5 = self.title("Even the signed refund event can change in transit.", 43)
        alice_note = speech_bubble("Refund sent: ₹ മലയാളം", PURPLE, size=29, max_width=4.5, font="Arial Unicode MS")
        alice_note.move_to([-3.25, 0.60, 0])
        bytes_ok = VGroup(code("exact UTF-8 bytes", 30, GREEN, "BOLD"), check(GREEN, 0.75))
        bytes_ok.arrange(RIGHT, buff=0.28).move_to([3.15, 0.85, 0])
        ascii_bad = VGroup(code("ASCII conversion", 30, RED, "BOLD"), strike(RED, 0.72))
        ascii_bad.arrange(RIGHT, buff=0.28).move_to([3.15, -0.30, 0])
        divider = Arrow([-0.55, 0.35, 0], [0.95, 0.35, 0], color=GREY, stroke_width=2.4)
        observed = display("All 16 non-ASCII deliveries verified only from the original bytes.", 32, WHITE)
        fit(observed, 11.4).move_to([0, -1.55, 0])
        remedy = display("Authenticate first. Parse second.", 44, YELLOW).move_to([0, -2.55, 0])
        assert_disjoint("webhook-bytes", title5, Group(alice_note, divider, bytes_ok, ascii_bad), observed, remedy, gap=0.14)
        self.play(Write(title5), FadeIn(alice_note), run_time=0.8)
        self.play(GrowArrow(divider), FadeIn(bytes_ok), run_time=0.8)
        self.play(FadeIn(ascii_bad), run_time=0.7)
        self.play(Write(observed), run_time=0.75)
        self.play(Write(remedy), run_time=0.7)
        self.finish()
