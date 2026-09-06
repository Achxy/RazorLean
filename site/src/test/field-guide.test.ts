/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { expect, test } from "vitest";
import { createCanvas } from "@napi-rs/canvas";
import { guideCases } from "../field-guide/cases";
import {
  paintPlate,
  PLATE_HEIGHT,
  PLATE_WIDTH,
} from "../field-guide/plate-renderer";
import { findings } from "../data/evidence";
import { excerptFor } from "../field-guide/source-excerpt";

test("every plate has a pinned official source excerpt surrounding its evidence line", () => {
  for (const finding of findings) {
    const excerpt = excerptFor(finding);
    expect(excerpt, finding.id).not.toBeNull();
    expect(excerpt!.commit).toMatch(/^[a-f0-9]{40}$/);
    expect(excerpt!.start).toBeGreaterThanOrEqual(1);
    expect(excerpt!.highlight).toBeGreaterThanOrEqual(excerpt!.start);
    expect(excerpt!.highlight).toBeLessThanOrEqual(excerpt!.end);
  }
});

test("every recorded finding has its own authored plate and explanation", () => {
  expect(new Set(guideCases.map((c) => c.id))).toEqual(
    new Set(findings.map((f) => f.id)),
  );
  expect(new Set(guideCases.map((c) => c.story)).size).toBe(findings.length);
  expect(new Set(guideCases.map((c) => c.mechanism)).size).toBe(
    findings.length,
  );
  expect(new Set(guideCases.map((c) => c.scope)).size).toBe(findings.length);
});
for (const item of guideCases) {
  test(`${item.id}: every stage fits and labels do not overlap`, () => {
    const canvas = createCanvas(PLATE_WIDTH, PLATE_HEIGHT);
    for (let step = 0; step < 4; step++) {
      const report = paintPlate(
        canvas.getContext("2d") as unknown as CanvasRenderingContext2D,
        item,
        step,
      );
      expect(report.outside, `stage ${step}: out of frame`).toEqual([]);
      expect(report.overlaps, `stage ${step}: overlapping text`).toEqual([]);
    }
  });
}
