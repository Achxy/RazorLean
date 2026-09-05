# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

from __future__ import annotations

from pathlib import Path

import numpy as np

from manim import (
    AnimationGroup,
    Arc,
    Arrow,
    Brace,
    Circle,
    Circumscribe,
    Create,
    Cross,
    CurvedArrow,
    DashedLine,
    Dot,
    DOWN,
    FadeIn,
    FadeOut,
    FadeTransform,
    Flash,
    Group,
    GrowArrow,
    GrowFromCenter,
    ImageMobject,
    Indicate,
    LaggedStart,
    LEFT,
    Line,
    MovingCameraScene,
    ORIGIN,
    Rectangle,
    ReplacementTransform,
    Restore,
    RIGHT,
    RoundedRectangle,
    ShowPassingFlash,
    Succession,
    SurroundingRectangle,
    Text,
    Transform,
    TransformFromCopy,
    TransformMatchingShapes,
    Underline,
    UP,
    VGroup,
    VMobject,
    Write,
    rate_functions,
)


# Color denotes a stable idea throughout the film; it is never decorative.
BLACK = "#0B0B0D"
WHITE = "#F4F1EA"
GREY = "#9C9A94"
DARK_GREY = "#34343A"
BLUE = "#58C4DD"
DEEP_BLUE = "#236B8E"
YELLOW = "#FFFF00"
GOLD = "#F0AC5F"
GREEN = "#83C167"
RED = "#FC6255"
MAROON = "#C55F73"
PURPLE = "#9A72AC"
TEAL = "#5CD0B3"

# STIX supplies the mathematical/editorial voice, Avenir the prose voice, and
# Menlo the source-code voice. No novelty handwritten font is used.
FONT = "Avenir Next"
SERIF = "STIX Two Text"
MONO = "Menlo"
ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
EASE = rate_functions.ease_in_out_sine
ENTER = rate_functions.ease_out_cubic

SAFE_LEFT = -6.78
SAFE_RIGHT = 6.78
SAFE_BOTTOM = -3.55
SAFE_TOP = 3.55


def txt(value: str, size: float = 32, color: str = WHITE, weight: str = "NORMAL", font: str = FONT) -> Text:
    return Text(value, font=font, font_size=size, color=color, weight=weight)


def display(value: str, size: float = 52, color: str = WHITE, weight: str = "NORMAL") -> Text:
    return txt(value, size, color, weight, SERIF)


def code(value: str, size: float = 26, color: str = WHITE, weight: str = "NORMAL") -> Text:
    return txt(value, size, color, weight, MONO)


def fit(mob, max_width: float, max_height: float | None = None):
    if mob.width > max_width:
        mob.scale_to_fit_width(max_width)
    if max_height is not None and mob.height > max_height:
        mob.scale_to_fit_height(max_height)
    return mob


def small_label(value: str, color: str = GREY) -> Text:
    return code(value.upper(), 15, color, "BOLD")


def ruled_label(value: str, color: str = BLUE) -> VGroup:
    label = small_label(value, color)
    rule = Line(ORIGIN, RIGHT * label.width, color=color, stroke_width=1.5)
    rule.next_to(label, DOWN, buff=0.055).align_to(label, LEFT)
    return VGroup(label, rule)


def stick_person(name: str, color: str, mood: str = "neutral", scale: float = 1.0) -> VGroup:
    """A deliberately simple recurring character, built from stable geometry."""
    head = Circle(radius=0.30, color=color, stroke_width=3).move_to([0, 0.82, 0])
    left_eye = Dot([-0.10, 0.88, 0], radius=0.025, color=color)
    right_eye = Dot([0.10, 0.88, 0], radius=0.025, color=color)
    if mood == "happy":
        mouth = Arc(radius=0.12, start_angle=np.pi, angle=np.pi, color=color, stroke_width=2)
        mouth.move_to([0, 0.76, 0])
    elif mood == "sad":
        mouth = Arc(radius=0.12, start_angle=0, angle=np.pi, color=color, stroke_width=2)
        mouth.move_to([0, 0.68, 0])
    else:
        mouth = Line([-0.09, 0.72, 0], [0.09, 0.72, 0], color=color, stroke_width=2)
    torso = Line([0, 0.52, 0], [0, -0.34, 0], color=color, stroke_width=3)
    arms = VMobject(stroke_color=color, stroke_width=3)
    arms.set_points_as_corners(
        [np.array([-0.48, 0.10, 0]), np.array([0, 0.34, 0]), np.array([0.48, 0.10, 0])]
    )
    left_leg = Line([0, -0.34, 0], [-0.38, -0.88, 0], color=color, stroke_width=3)
    right_leg = Line([0, -0.34, 0], [0.38, -0.88, 0], color=color, stroke_width=3)
    label = display(name, 28, color, "BOLD").move_to([0, -1.20, 0])
    person = VGroup(head, left_eye, right_eye, mouth, torso, arms, left_leg, right_leg, label)
    person.scale(scale)
    return person


def speech_bubble(
    value: str,
    color: str,
    *,
    size: float = 31,
    max_width: float = 4.8,
    padding_x: float = 0.36,
    padding_y: float = 0.24,
    font: str = SERIF,
) -> VGroup:
    """Build a speech bubble from its text bounds and prove the padding exists."""
    words = fit(txt(value, size, WHITE, font=font), max_width - 2 * padding_x)
    frame = RoundedRectangle(
        width=words.width + 2 * padding_x,
        height=words.height + 2 * padding_y,
        corner_radius=0.16,
        color=color,
        stroke_width=2.2,
    )
    words.move_to(frame)
    tail = VMobject(stroke_color=color, stroke_width=2.2)
    tail.set_points_as_corners(
        [
            frame.get_bottom() + LEFT * 0.36,
            frame.get_bottom() + LEFT * 0.18 + DOWN * 0.28,
            frame.get_bottom() + RIGHT * 0.02,
        ]
    )
    assert_contains("speech-bubble-padding", frame, words, tolerance=-min(padding_x, padding_y) * 0.35)
    return VGroup(frame, tail, words)


def padded_frame(
    content,
    color: str = BLUE,
    *,
    padding_x: float = 0.48,
    padding_y: float = 0.34,
    corner_radius: float = 0.16,
    stroke_width: float = 2.2,
) -> VGroup:
    """Create a content-sized frame; unlike a decorative box, it cannot overflow."""
    frame = RoundedRectangle(
        width=content.width + 2 * padding_x,
        height=content.height + 2 * padding_y,
        corner_radius=corner_radius,
        color=color,
        stroke_width=stroke_width,
    ).move_to(content)
    assert_contains("padded-frame", frame, content, tolerance=-min(padding_x, padding_y) * 0.35)
    return VGroup(frame, content)


def check(color: str = GREEN, scale: float = 1.0) -> VMobject:
    mark = VMobject(stroke_color=color, stroke_width=6 * scale)
    mark.set_points_as_corners(
        [np.array([-0.28, 0.00, 0]), np.array([-0.06, -0.22, 0]), np.array([0.35, 0.28, 0])]
    )
    return mark


def strike(color: str = RED, scale: float = 1.0) -> VMobject:
    mark = VMobject(stroke_color=color, stroke_width=5 * scale)
    mark.set_points_as_corners(
        [np.array([-0.25, -0.25, 0]), np.array([0.25, 0.25, 0]), np.array([0, 0, 0]), np.array([-0.25, 0.25, 0]), np.array([0.25, -0.25, 0])]
    )
    return mark


def source_image(filename: str, max_width: float, max_height: float, border_color: str = DARK_GREY) -> Group:
    image = ImageMobject(str(ASSET_DIR / "evidence" / filename))
    fit(image, max_width, max_height)
    border = SurroundingRectangle(image, color=border_color, buff=0.035, stroke_width=1.8)
    return Group(image, border)


def image_region(
    image: ImageMobject,
    bounds: tuple[float, float, float, float],
    pixel_size: tuple[float, float],
    color: str,
    stroke_width: float = 3.0,
) -> Rectangle:
    """Return an exact pixel-to-scene highlight with no decorative padding."""
    x0, y0, x1, y1 = bounds
    pixel_width, pixel_height = pixel_size
    if not (0 <= x0 < x1 <= pixel_width and 0 <= y0 < y1 <= pixel_height):
        raise ValueError(f"highlight {bounds} is outside source image {pixel_size}")
    width = (x1 - x0) / pixel_width * image.width
    height = (y1 - y0) / pixel_height * image.height
    center_x = image.get_left()[0] + (x0 + x1) / (2 * pixel_width) * image.width
    center_y = image.get_top()[1] - (y0 + y1) / (2 * pixel_height) * image.height
    box = Rectangle(width=width, height=height, color=color, stroke_width=stroke_width)
    box.move_to([center_x, center_y, image.get_center()[2]])
    assert_contains("image-region", image, box, tolerance=0.02)
    return box


def assert_contains(name: str, outer, inner, tolerance: float = 0.0) -> None:
    if inner.get_left()[0] < outer.get_left()[0] - tolerance:
        raise ValueError(f"{name}: inner object crosses left edge")
    if inner.get_right()[0] > outer.get_right()[0] + tolerance:
        raise ValueError(f"{name}: inner object crosses right edge")
    if inner.get_bottom()[1] < outer.get_bottom()[1] - tolerance:
        raise ValueError(f"{name}: inner object crosses bottom edge")
    if inner.get_top()[1] > outer.get_top()[1] + tolerance:
        raise ValueError(f"{name}: inner object crosses top edge")


def assert_in_frame(name: str, *mobjects) -> None:
    for index, mob in enumerate(mobjects):
        if mob.get_left()[0] < SAFE_LEFT or mob.get_right()[0] > SAFE_RIGHT:
            raise ValueError(f"{name}[{index}] crosses horizontal safe area")
        if mob.get_bottom()[1] < SAFE_BOTTOM or mob.get_top()[1] > SAFE_TOP:
            raise ValueError(f"{name}[{index}] crosses vertical safe area")


def assert_disjoint(name: str, *mobjects, gap: float = 0.06) -> None:
    """Fail the render when independent layout regions overlap."""
    assert_in_frame(name, *mobjects)
    for i, first in enumerate(mobjects):
        for j, second in enumerate(mobjects[i + 1 :], start=i + 1):
            horizontal_gap = max(
                second.get_left()[0] - first.get_right()[0],
                first.get_left()[0] - second.get_right()[0],
            )
            vertical_gap = max(
                second.get_bottom()[1] - first.get_top()[1],
                first.get_bottom()[1] - second.get_top()[1],
            )
            if horizontal_gap < gap and vertical_gap < gap:
                raise ValueError(f"{name}: regions {i} and {j} overlap")


class ProofScene(MovingCameraScene):
    TARGET = 10.0

    def setup(self):
        super().setup()
        self.camera.background_color = BLACK
        self._scene_started_at = self.renderer.time

    def chapter(self, number: str, title: str) -> VGroup:
        n = code(number, 18, BLUE, "BOLD")
        name = small_label(title, GREY)
        group = VGroup(n, name).arrange(RIGHT, buff=0.18)
        group.to_corner(UP + LEFT, buff=0.50)
        return group

    def title(self, value: str, size: float = 43, color: str = WHITE) -> Text:
        title = fit(display(value, size, color), 12.2)
        title.move_to([0, 2.78, 0])
        return title

    def clear(self, *mobjects, run_time: float = 0.45):
        self.play(FadeOut(Group(*mobjects), shift=UP * 0.08), run_time=run_time)

    def finish(self):
        elapsed = self.renderer.time - self._scene_started_at
        if elapsed < self.TARGET:
            self.wait(self.TARGET - elapsed)
