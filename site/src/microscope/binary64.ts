/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { exactMinor } from "../components/payment-model";

export type Fraction = { numerator: bigint; denominator: bigint };
export function subtract(a: Fraction, b: Fraction): Fraction {
  return {
    numerator: a.numerator * b.denominator - b.numerator * a.denominator,
    denominator: a.denominator * b.denominator,
  };
}
export function approximate(value: Fraction) {
  return Number(value.numerator) / Number(value.denominator);
}
export function binary64(value: number) {
  if (!Number.isFinite(value)) throw new Error("A finite number is required.");
  const view = new DataView(new ArrayBuffer(8));
  view.setFloat64(0, value, false);
  const word = view.getBigUint64(0, false);
  const exponentBits = Number((word >> 52n) & 2047n);
  const fractionBits = word & ((1n << 52n) - 1n);
  const exponent = (exponentBits || 1) - 1023;
  let numerator = (exponentBits ? 1n << 52n : 0n) + fractionBits;
  let denominator = 1n;
  const shift = exponent - 52;
  if (shift >= 0) numerator <<= BigInt(shift);
  else denominator <<= BigInt(-shift);
  if (word >> 63n) numerator = -numerator;
  return {
    word,
    bits: word.toString(2).padStart(64, "0"),
    exponent,
    fractionBits,
    numerator,
    denominator,
  };
}
export function adjacent(value: number, direction: -1 | 1) {
  if (!Number.isFinite(value) || value <= 0)
    throw new Error("Use a positive finite value.");
  const view = new DataView(new ArrayBuffer(8));
  view.setFloat64(0, value, false);
  view.setBigUint64(0, view.getBigUint64(0, false) + BigInt(direction), false);
  return view.getFloat64(0, false);
}
export function decimal(value: Fraction): string {
  const negative = value.numerator < 0n;
  const magnitude = negative ? -value.numerator : value.numerator;
  let remainder = magnitude % value.denominator;
  let tail = "";
  // Every binary64 denominator is a power of two; decimal expansion terminates.
  while (remainder && tail.length < 1075) {
    remainder *= 10n;
    tail += String(remainder / value.denominator);
    remainder %= value.denominator;
  }
  return `${negative ? "−" : ""}${magnitude / value.denominator}${tail ? `.${tail}` : ""}`;
}
export function priceFromPaise(paise: number) {
  const n = BigInt(paise);
  return `${n / 100n}.${String(n % 100n).padStart(2, "0")}`;
}
export function inspectPrice(price: string) {
  if (!/^\d{1,4}(\.\d{1,2})?$/.test(price))
    throw new Error(
      "Enter ₹0.01 to ₹9,999.99, with at most two decimal places.",
    );
  const intended = exactMinor(price, "INR");
  const input = binary64(Number(price));
  const multiplied = Number(price) * 100;
  const product = binary64(multiplied);
  const target = { numerator: intended, denominator: 1n };
  const error = subtract(product, target);
  const targetValue = Number(intended);
  const ulp = adjacent(targetValue, 1) - targetValue;
  return {
    price,
    intended,
    input,
    product,
    multiplied,
    error,
    ulp,
    inputError: subtract(input, { numerator: intended, denominator: 100n }),
    truncated: BigInt(Math.trunc(multiplied)),
    rounded: BigInt(Math.round(multiplied)),
    exactProduct: decimal(product),
    exactInput: decimal(input),
  };
}
export type PriceInspection = ReturnType<typeof inspectPrice>;
export function microscopeView(
  model: PriceInspection,
  zoom: number,
  width: number,
) {
  const boundedZoom = Math.max(0, Math.min(1, zoom));
  const span = 4 * Math.pow((model.ulp * 8) / 4, boundedZoom);
  const left = 30,
    right = width - 30,
    center = (left + right) / 2;
  const pixelsPerUnit = (right - left) / span;
  return {
    span,
    left,
    right,
    center,
    pixelsPerUnit,
    actualX: center + approximate(model.error) * pixelsPerUnit,
    magnification: 4 / span,
    gridSpacing: model.ulp * pixelsPerUnit,
  };
}
