/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { expect, test } from "vitest";
import {
  convert,
  exactMinor,
  inspectProgram,
  retrySnapshot,
} from "../components/payment-model";

test("separates truncation, rounding and currency-aware conversion", () => {
  expect(convert("2.01", "INR", "truncate")).toBe(200n);
  expect(convert("2.01", "INR", "round")).toBe(201n);
  expect(convert("295", "JPY", "round")).toBe(29500n);
  expect(convert("295", "JPY", "exact")).toBe(295n);
  expect(convert("295.990", "KWD", "exact")).toBe(295990n);
});
test("decimal parsing rejects excess precision and unsupported quantum", () => {
  expect(() => exactMinor("1.01", "JPY")).toThrow(/decimal places/);
  expect(() => exactMinor("2.001", "KWD")).toThrow(/last subunit/);
  for (const bad of [
    "NaN",
    "Infinity",
    "-2",
    "1e2",
    "0",
    "1.0000",
    "99999999999",
  ])
    expect(() => exactMinor(bad, "INR")).toThrow();
  expect(exactMinor("9999999999.99", "INR")).toBe(999999999999n);
});
test("lost acknowledgement does not erase the committed effect", () => {
  expect(retrySnapshot(3, false)).toMatchObject({
    effects: 1,
    known: false,
    requests: 1,
  });
  expect(retrySnapshot(6, false)).toMatchObject({ effects: 2, requests: 2 });
  expect(retrySnapshot(6, true)).toMatchObject({
    effects: 1,
    requests: 2,
    replayed: true,
  });
});
test("checks authentication and business preconditions before effects", () => {
  expect(inspectProgram(["decode", "verify", "match", "consume"]).ok).toBe(
    false,
  );
  expect(inspectProgram(["verify", "decode", "consume", "match"]).ok).toBe(
    false,
  );
  expect(inspectProgram(["verify", "match", "decode", "consume"]).ok).toBe(
    false,
  );
  expect(inspectProgram(["verify", "decode", "match", "consume"]).ok).toBe(
    true,
  );
});
