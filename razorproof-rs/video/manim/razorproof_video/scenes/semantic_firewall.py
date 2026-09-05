# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

from ..shared import *  # noqa: F401,F403


class SemanticFirewall(ProofScene):
    TARGET = 47.0

    def construct(self):
        title = self.title("Alice needs one promise that survives the whole trip.", 43)
        alice = stick_person("ALICE", PURPLE, "neutral", 0.92).move_to([-4.6, -0.78, 0])
        bob = stick_person("BOB", BLUE, "neutral", 0.92).move_to([4.6, -0.78, 0])
        fields = [
            ("price", "201 INR subunits", YELLOW),
            ("parties", "Alice → Bob", PURPLE),
            ("effect", "fulfil this purchase once", GOLD),
            ("evidence", "original callback bytes", GREEN),
        ]
        rows = VGroup()
        for label, value, color in fields:
            left = code(label, 23, color, "BOLD")
            right = txt(value, 27, WHITE)
            row = VGroup(left, right).arrange(RIGHT, buff=0.62)
            assert_disjoint(f"intent-field-{label}", *row, gap=0.28)
            rows.add(row)
        rows.arrange(DOWN, aligned_edge=LEFT, buff=0.31)
        fit(rows, 7.7)
        name = code("PaymentIntent", 31, BLUE, "BOLD")
        content = VGroup(name, rows).arrange(DOWN, buff=0.36)
        envelope = padded_frame(content, BLUE, padding_x=0.48, padding_y=0.34)
        envelope.move_to([0, -0.10, 0])
        left_arrow = Arrow(alice.get_right(), envelope.get_left(), buff=0.24, color=PURPLE, stroke_width=2.5)
        right_arrow = Arrow(envelope.get_right(), bob.get_left(), buff=0.24, color=BLUE, stroke_width=2.5)
        assert_contains("intent-envelope-final", envelope[0], envelope[1], tolerance=-0.10)
        assert_disjoint("intent-story", title, Group(alice, left_arrow, envelope, right_arrow, bob), gap=0.12)
        self.play(Write(title), FadeIn(alice), FadeIn(bob), run_time=0.9)
        self.play(GrowArrow(left_arrow), Create(envelope[0]), FadeIn(envelope[1]), run_time=1.1)
        self.play(GrowArrow(right_arrow), run_time=0.65)
        self.wait(9.0)
        self.clear(title, alice, bob, left_arrow, right_arrow, envelope)

        title2 = self.title("Before Razorpay sees a request, the promise is checked.", 43)
        alice_value = VGroup(small_label("ALICE'S PROMISE", PURPLE), display("201", 61, YELLOW, "BOLD"))
        request_value = VGroup(small_label("OUTGOING REQUEST", BLUE), display("200", 61, RED, "BOLD"))
        alice_value.arrange(DOWN, buff=0.22).move_to([-4.15, 0.30, 0])
        request_value.arrange(DOWN, buff=0.22).move_to([4.15, 0.30, 0])
        compare_content = VGroup(
            code("201 ≠ 200", 40, RED, "BOLD"),
            VGroup(strike(RED, 0.78), small_label("BLOCK", RED)).arrange(RIGHT, buff=0.25),
        ).arrange(DOWN, buff=0.35)
        firewall = padded_frame(compare_content, RED, padding_x=0.38, padding_y=0.30)
        firewall.move_to([0, 0.23, 0])
        left_arrow = Arrow(alice_value.get_right(), firewall.get_left(), buff=0.20, color=YELLOW, stroke_width=2.5)
        right_arrow = Arrow(firewall.get_right(), request_value.get_left(), buff=0.20, color=RED, stroke_width=2.5)
        right_arrow.set_opacity(0.28)
        consequence = display("The wrong order never reaches the provider.", 43, GREEN).move_to([0, -2.10, 0])
        detail = txt("The day-zero bug becomes a deterministic rejection.", 31, WHITE).move_to([0, -2.83, 0])
        assert_contains("firewall-content", firewall[0], firewall[1], tolerance=-0.08)
        assert_disjoint("firewall-compare", title2, Group(alice_value, left_arrow, firewall, right_arrow, request_value), consequence, detail, gap=0.13)
        self.play(Write(title2), FadeIn(alice_value), run_time=0.85)
        self.play(GrowArrow(left_arrow), Create(firewall[0]), FadeIn(firewall[1]), run_time=1.0)
        self.play(Create(right_arrow), FadeIn(request_value), run_time=0.75)
        self.play(Write(consequence), run_time=0.75)
        self.play(Write(detail), run_time=0.65)
        self.wait(9.0)
        self.clear(title2, alice_value, request_value, firewall, left_arrow, right_arrow, consequence, detail)

        title3 = self.title("The same promise controls success after Bob pays.", 43)
        stages = VGroup(
            VGroup(stick_person("ALICE", PURPLE, "neutral", 0.55), small_label("QUOTED", YELLOW)),
            VGroup(code("ORDER", 27, BLUE, "BOLD"), small_label("CREATED", BLUE)),
            VGroup(stick_person("BOB", BLUE, "happy", 0.55), small_label("CAPTURED", GREEN)),
            VGroup(check(GREEN, 0.85), small_label("FULFILLED ONCE", PURPLE)),
        )
        for stage in stages:
            stage.arrange(DOWN, buff=0.24)
        stages.arrange(RIGHT, buff=1.10).move_to([0, 0.10, 0])
        assert_disjoint("lifecycle-stages", *stages, gap=0.55)
        arrows = VGroup()
        for left, right in zip(stages[:-1], stages[1:]):
            arrows.add(Arrow(left.get_right(), right.get_left(), buff=0.18, color=GREY, stroke_width=2.3))
        rule = display("Each transition re-checks the same intent.", 42, YELLOW).move_to([0, -2.35, 0])
        assert_disjoint("lifecycle", title3, Group(stages, arrows), rule, gap=0.15)
        self.play(Write(title3), run_time=0.75)
        self.play(FadeIn(stages[0]), run_time=0.5)
        for arrow, stage in zip(arrows, stages[1:]):
            self.play(GrowArrow(arrow), FadeIn(stage), run_time=0.75)
        self.play(Write(rule), run_time=0.75)
        self.wait(9.0)
        self.clear(title3, stages, arrows, rule)

        title4 = self.title("Four hard boundaries become one service.", 46)
        capabilities = VGroup(
            VGroup(code("MONEY", 28, YELLOW, "BOLD"), txt("currency-aware integer conversion", 28, WHITE)),
            VGroup(code("PAYMENT", 28, GREEN, "BOLD"), txt("provider re-fetch before fulfilment", 28, WHITE)),
            VGroup(code("RETRY", 28, GOLD, "BOLD"), txt("one stable identity per effect", 28, WHITE)),
            VGroup(code("WEBHOOK", 28, BLUE, "BOLD"), txt("verify original bytes before parsing", 28, WHITE)),
        )
        for row in capabilities:
            row.arrange(RIGHT, buff=0.65)
            assert_disjoint("capability-row", *row, gap=0.30)
        capabilities.arrange(DOWN, aligned_edge=LEFT, buff=0.48).move_to([0, 0.20, 0])
        fit(capabilities, 9.25)
        name = code("RAZORPROOF", 34, BLUE, "BOLD")
        name_rule = Line(LEFT * name.width / 2, RIGHT * name.width / 2, color=BLUE, stroke_width=1.8)
        brand = VGroup(name, name_rule).arrange(DOWN, buff=0.10)
        stack = VGroup(brand, capabilities).arrange(DOWN, buff=0.34).move_to([0, 0.12, 0])
        result = display("Meaning enters once. Every boundary must preserve it.", 38, GREEN)
        fit(result, 11.6).move_to([0, -2.70, 0])
        assert_disjoint("capabilities", title4, stack, result, gap=0.14)
        self.play(Write(title4), FadeIn(name), Create(name_rule), run_time=0.85)
        self.play(LaggedStart(*[FadeIn(row, shift=RIGHT * 0.08) for row in capabilities], lag_ratio=0.16), run_time=1.4)
        self.play(Write(result), run_time=0.75)
        self.finish()
