/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { expect, test } from "vitest";
import { createCanvas } from "@napi-rs/canvas";
import {
  adjacent,
  approximate,
  binary64,
  decimal,
  inspectPrice,
  microscopeView,
  priceFromPaise,
} from "../microscope/binary64";
import { drawRuler, RULER_HEIGHT } from "../microscope/draw-ruler";

test("decodes known IEEE 754 patterns and their exact decimal values", () => {
  expect(binary64(1).word).toBe(0x3ff0000000000000n);
  expect(binary64(2.5).word).toBe(0x4004000000000000n);
  expect(decimal(binary64(2.5))).toBe("2.5");
  expect(decimal(binary64(0.1))).toBe(
    "0.1000000000000000055511151231257827021181583404541015625",
  );
  expect(binary64(-0).bits[0]).toBe("1");
  expect(decimal(binary64(-2.5))).toBe("−2.5");
  expect(binary64(Number.MIN_VALUE).numerator).toBe(1n);
  expect(binary64(Number.MIN_VALUE).denominator).toBe(1n << 1074n);
  expect(() => binary64(Infinity)).toThrow();
});
test("the ₹2.01 gap is derived from exact fractions, not display formatting", () => {
  const model = inspectPrice("2.01");
  expect(model.exactInput).toBe(
    "2.0099999999999997868371792719699442386627197265625",
  );
  expect(model.exactProduct).toBe(
    "200.999999999999971578290569595992565155029296875",
  );
  expect(model.truncated).toBe(200n);
  expect(model.rounded).toBe(201n);
  expect(model.intended).toBe(201n);
  expect(approximate(model.error)).toBe(-model.ulp);
  expect(adjacent(model.multiplied, 1)).toBe(201);
});
test("the diagram magnifies a real distance and coincident values stay coincident", () => {
  const model = inspectPrice("2.01");
  const ordinary = microscopeView(model, 0, 900),
    magnified = microscopeView(model, 1, 900);
  expect(Math.abs(ordinary.actualX - ordinary.center)).toBeLessThan(0.001);
  expect(magnified.center - magnified.actualX).toBeCloseTo(
    magnified.gridSpacing,
    8,
  );
  expect(magnified.center - magnified.actualX).toBeGreaterThan(80);
  const exact = microscopeView(inspectPrice("2.50"), 1, 900);
  expect(exact.actualX).toBe(exact.center);
});
test("all scrubber prices retain decimal intent and decode to the original numbers", () => {
  for (let paise = 100; paise <= 300; paise++) {
    const price = priceFromPaise(paise),
      model = inspectPrice(price);
    expect(model.intended).toBe(BigInt(paise));
    expect(Number(model.exactInput)).toBe(Number(price));
    expect(Number(model.exactProduct)).toBe(Number(price) * 100);
    expect(model.truncated).toBe(BigInt(Math.trunc(Number(price) * 100)));
  }
  expect(inspectPrice("2.50").error.numerator).toBe(0n);
  for (const bad of ["", "0", "NaN", "Infinity", "-1", "1e2", "2.001", "10000"])
    expect(() => inspectPrice(bad)).toThrow();
});
for (const width of [320, 358, 560, 900]) {
  test(`ruler labels fit at ${width}px across prices and magnifications`, () => {
    const canvas = createCanvas(width, RULER_HEIGHT);
    for (const price of [
      "0.01",
      "1.28",
      "2.01",
      "2.02",
      "2.50",
      "10.24",
      "9999.99",
    ]) {
      for (let i = 0; i <= 20; i++) {
        const report = drawRuler(
          canvas.getContext("2d") as unknown as CanvasRenderingContext2D,
          inspectPrice(price),
          i / 20,
          width,
        );
        expect(report.outside, `${price} at ${i / 20}`).toEqual([]);
        expect(report.overlaps, `${price} at ${i / 20}`).toEqual([]);
      }
    }
  });
}
