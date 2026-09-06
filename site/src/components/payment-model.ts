/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
export const units = { INR: 2, JPY: 0, KWD: 3 } as const;
export type Currency = keyof typeof units;
export type Rule = "truncate" | "round" | "exact";

export function exactMinor(input: string, currency: Currency): bigint {
  if (!/^\d{1,10}(\.\d{1,3})?$/.test(input))
    throw new Error(
      "Use a positive decimal amount, up to 10 whole digits and 3 decimal places.",
    );
  const [whole, fraction = ""] = input.split(".");
  const exponent = units[currency];
  if (fraction.slice(exponent).replace(/0/g, ""))
    throw new Error(
      `${currency} has ${exponent} decimal places; this amount cannot be represented exactly.`,
    );
  const value =
    BigInt(whole) * 10n ** BigInt(exponent) +
    BigInt(fraction.slice(0, exponent).padEnd(exponent, "0") || "0");
  if (value <= 0n) throw new Error("The price must be greater than zero.");
  if (currency === "KWD" && value % 10n !== 0n)
    throw new Error(
      "This KWD provider contract requires the last subunit digit to be zero.",
    );
  return value;
}

export function convert(input: string, currency: Currency, rule: Rule): bigint {
  const exact = exactMinor(input, currency);
  if (rule === "exact") return exact;
  return BigInt(
    rule === "round"
      ? Math.round(Number(input) * 100)
      : Math.trunc(Number(input) * 100),
  );
}

export function retrySnapshot(step: number, protectedEffect: boolean) {
  return {
    requests: step < 1 ? 0 : step < 4 ? 1 : 2,
    effects: step < 2 ? 0 : step < 5 || protectedEffect ? 1 : 2,
    known: step >= 6,
    replayed: step >= 5 && protectedEffect,
  };
}

export type Block = "decode" | "verify" | "match" | "consume";
export const blockNames: Record<Block, string> = {
  decode: "Decode the event",
  verify: "Verify original bytes",
  match: "Match Bob’s quote",
  consume: "Consume the intent once",
};
export function inspectProgram(blocks: Block[]) {
  const completed = new Set<Block>();
  for (const [stop, block] of blocks.entries()) {
    if (block === "decode" && !completed.has("verify"))
      return {
        stop,
        ok: false,
        message:
          "Stop: decoding before authentication permits the original signed representation to be lost. Verify the untouched bytes first.",
      };
    if (block === "match" && !completed.has("decode"))
      return {
        stop,
        ok: false,
        message:
          "Stop: the quote check needs the decoded event. Decode the authenticated bytes before matching.",
      };
    if (block === "consume" && !completed.has("match"))
      return {
        stop,
        ok: false,
        message:
          "Stop: the fulfillment effect happened before the event was matched to Bob’s quote. Authentication is not permission to fulfill.",
      };
    completed.add(block);
  }
  return {
    stop: 3,
    ok: true,
    message:
      "The modeled boundary is in order: authenticate, decode, match, consume once. This checks sequencing, not the implementation of each block.",
  };
}
