/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { useState } from "react";
import { motion } from "motion/react";
import type { PriceInspection } from "./binary64";
import {
  convert,
  exactMinor,
  type Currency,
  type Rule,
} from "../components/payment-model";

export function ConversionBench({ model }: { model: PriceInspection }) {
  const [rule, setRule] = useState<Rule>("truncate");
  const result =
    rule === "truncate"
      ? model.truncated
      : rule === "round"
        ? model.rounded
        : model.intended;
  const difference = result - model.intended;
  return (
    <div className="conversion-bench">
      <div
        className="instrument-tabs"
        role="group"
        aria-label="Choose an integer conversion"
      >
        {(["truncate", "round", "exact"] as const).map((name, i) => (
          <button
            key={name}
            aria-pressed={rule === name}
            onClick={() => setRule(name)}
          >
            {
              [
                "Discard the fraction",
                "Round to nearest",
                "Keep decimal intent",
              ][i]
            }
          </button>
        ))}
      </div>
      <div className="conversion-operation">
        <span>
          {rule === "exact"
            ? `decimal string “${model.price}”`
            : model.multiplied.toPrecision(17)}
        </span>
        <span className="operator">
          {rule === "exact"
            ? "parse digits →"
            : rule === "round"
              ? "round →"
              : "truncate →"}
        </span>
        <motion.output
          key={String(result)}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className={difference === 0n ? "money-preserved" : "money-changed"}
          data-testid="conversion-result"
        >
          {String(result)}
          <small>paise</small>
        </motion.output>
      </div>
      <p className="conversion-verdict" aria-live="polite">
        {difference === 0n
          ? rule === "exact"
            ? "The integer comes directly from decimal digits. There is no binary fraction to discard."
            : "This price survives this conversion. Change the price above to test a different case."
          : `The order is ${difference < 0n ? -difference : difference} paise ${difference < 0n ? "below" : "above"} Alice’s agreed price. The integer is valid; the translation is wrong.`}
      </p>
      <div className="boundary-line">
        <span>integration code</span>
        <span>integer request crosses this boundary</span>
        <span>provider API</span>
      </div>
      <p className="instrument-note">
        Computed locally. No payment request is sent. Rounding repairs this
        example; it does not establish a general money policy.
      </p>
    </div>
  );
}

const currencies = {
  INR: { price: "2.01", symbol: "₹", unit: "paise", exponent: 2 },
  JPY: { price: "295", symbol: "¥", unit: "yen", exponent: 0 },
  KWD: { price: "295.990", symbol: "KD ", unit: "fils", exponent: 3 },
} as const;
export function UnitBench() {
  const [currency, setCurrency] = useState<Currency>("JPY");
  const [aware, setAware] = useState(false);
  const spec = currencies[currency];
  const correct = exactMinor(spec.price, currency),
    sent = convert(spec.price, currency, aware ? "exact" : "round");
  const decimalDigits = spec.price.split(".");
  return (
    <div className="unit-bench">
      <div
        className="instrument-tabs"
        role="group"
        aria-label="Choose a currency"
      >
        {Object.keys(currencies).map((c) => (
          <button
            key={c}
            aria-pressed={currency === c}
            onClick={() => setCurrency(c as Currency)}
          >
            {c}
          </button>
        ))}
      </div>
      <div className="decimal-conveyor">
        <span className="conveyor-price">
          {spec.symbol}
          {decimalDigits[0]}
          {decimalDigits[1] && (
            <>
              <i>.</i>
              {decimalDigits[1]}
            </>
          )}
        </span>
        <div className="conveyor-teeth" aria-hidden="true">
          {Array.from({ length: 25 }, (_, i) => (
            <span key={i} style={{ height: i % 5 === 0 ? 24 : 12 }} />
          ))}
        </div>
        <span className="conveyor-ratio">
          {aware ? `× ${10 ** spec.exponent}` : "× 100"}
        </span>
        <output
          data-testid="unit-result"
          className={sent === correct ? "money-preserved" : "money-changed"}
        >
          {String(sent)}
          <small>{spec.unit}</small>
        </output>
      </div>
      <label className="unit-switch">
        <input
          type="checkbox"
          checked={aware}
          onChange={(event) => setAware(event.target.checked)}
        />{" "}
        Let the currency choose the unit
      </label>
      <p aria-live="polite">
        {sent === correct
          ? `${spec.symbol}${spec.price} becomes ${correct} ${spec.unit}. ${aware ? "The conversion respects the currency’s exponent." : "Two decimal places happen to be right for INR."}`
          : `${spec.symbol}${spec.price} should be ${correct} ${spec.unit}, not ${sent}. Rounding cannot repair the wrong unit.`}
      </p>
      <p className="instrument-note">
        KWD uses three decimal places; the recorded Razorpay contract also
        requires a zero final subunit digit. This example satisfies that rule.
      </p>
    </div>
  );
}
