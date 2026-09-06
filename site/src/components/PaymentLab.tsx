/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { convert, exactMinor, units } from "./payment-model";
import type { Currency, Rule } from "./payment-model";
import { useSequence } from "./useSequence";

const presets = { JPY: "295", INR: "2.01", KWD: "295.990" };
const xs = [65, 290, 515, 740];

export function PaymentLab() {
  const [amount, setAmount] = useState("295");
  const [currency, setCurrency] = useState<Currency>("JPY");
  const [rule, setRule] = useState<Rule>("truncate");
  const seq = useSequence(3, 1500);
  const reduced = useReducedMotion();
  let intended = 0n,
    actual = 0n,
    error = "";
  try {
    intended = exactMinor(amount, currency);
    actual = convert(amount, currency, rule);
  } catch (e) {
    error = (e as Error).message;
  }
  const wrong = intended !== actual;
  const describe = [
    `Alice agrees to ${amount} ${currency}. Bob’s catalogue is the starting point.`,
    rule === "exact"
      ? `Read the decimal string using ${currency}’s exponent ${units[currency]}. No binary floating point is needed.`
      : `The integration computes ${Number(amount) * 100}, then ${rule === "truncate" ? "discards the fraction" : "rounds"}. It assumes every currency has two decimal places.`,
    `The outgoing order contains ${actual} subunits. ${currency} requires ${intended} for Bob’s price.`,
    wrong
      ? `The arithmetic changed the order by ${actual - intended} subunits. A successful order response would not repair that mismatch.`
      : "The outgoing integer preserves Bob’s price. This solves the conversion step, not every payment invariant.",
  ];
  return (
    <div className="lab payment-lab" id="failure">
      <div className="lab-inputs">
        <label>
          Bob’s price
          <input
            aria-label="Bob’s price"
            inputMode="decimal"
            value={amount}
            onChange={(e) => {
              setAmount(e.target.value);
              seq.reset();
            }}
          />
        </label>
        <label>
          Currency
          <select
            value={currency}
            onChange={(e) => {
              const c = e.target.value as Currency;
              setCurrency(c);
              setAmount(presets[c]);
              seq.reset();
            }}
          >
            {Object.keys(units).map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
        </label>
        <label>
          Conversion block
          <select
            value={rule}
            onChange={(e) => {
              setRule(e.target.value as Rule);
              seq.reset();
            }}
          >
            <option value="truncate">truncate(amount × 100)</option>
            <option value="round">round(amount × 100)</option>
            <option value="exact">RazorProof: exact decimal</option>
          </select>
        </label>
      </div>
      <div className="diagram-scroll">
        <svg
          viewBox="0 0 810 220"
          className="flow-canvas"
          role="img"
          aria-label={`Payment trace. Stage ${seq.step + 1}. ${error || describe[seq.step]}`}
        >
          <defs>
            <marker
              id="payment-arrow"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M0 0L10 5L0 10" fill="#66665f" />
            </marker>
          </defs>
          {[0, 1, 2].map((i) => (
            <g key={i}>
              <path
                d={`M${xs[i] + 31} 101H${xs[i + 1] - 36}`}
                stroke="#42423c"
                markerEnd="url(#payment-arrow)"
              />
              <motion.path
                d={`M${xs[i] + 31} 101H${xs[i + 1] - 36}`}
                stroke={wrong && i > 0 ? "#dd745f" : "#81a981"}
                strokeWidth="2"
                initial={false}
                animate={{ pathLength: seq.step > i ? 1 : 0 }}
                transition={{ duration: reduced ? 0 : 0.6 }}
              />
            </g>
          ))}
          {xs.map((x, i) => (
            <g key={x}>
              {i === 0 || i === 3 ? (
                <g
                  stroke={i === 0 ? "#b89ab8" : "#95aeca"}
                  strokeWidth="1.5"
                  fill="none"
                >
                  <circle cx={x} cy="74" r="14" />
                  <path
                    d={`M${x} 88v35m0-22l-22 15m22-15l22 15m-22 7l-20 24m20-24l20 24`}
                  />
                </g>
              ) : (
                <rect
                  x={x - 27}
                  y="76"
                  width="54"
                  height="50"
                  rx="8"
                  fill="#141413"
                  stroke={seq.step >= i ? "#b58d68" : "#57564e"}
                />
              )}
              <text x={x} y="40" textAnchor="middle">
                {["Alice", "Integration", "Order API", "Bob"][i]}
              </text>
              <text
                x={x}
                y="178"
                textAnchor="middle"
                style={{ fontSize: amount.length > 9 ? 12 : 17 }}
                className={i > 1 && wrong && seq.step >= 2 ? "bad-text" : ""}
              >
                {i === 0
                  ? `${amount} ${currency}`
                  : i === 1
                    ? rule === "exact"
                      ? `× 10${["⁰", "¹", "²", "³"][units[currency]]}`
                      : "× 100"
                    : seq.step >= 2
                      ? i === 2
                        ? `${actual} subunits`
                        : wrong
                          ? "price changed"
                          : "price preserved"
                      : "waiting"}
              </text>
            </g>
          ))}
          {!error && (
            <motion.circle
              r="6"
              cy="101"
              initial={false}
              animate={{ cx: xs[seq.step] }}
              transition={{ duration: reduced ? 0 : 0.8, ease: "easeInOut" }}
              fill="#e8ca91"
              stroke="#141413"
              strokeWidth="3"
            />
          )}
          <text x="405" y="207" textAnchor="middle" className="diagram-note">
            Follow the amount, not the success status.
          </text>
        </svg>
      </div>
      <div className="transport">
        <button className="run" onClick={seq.toggle} disabled={!!error}>
          {seq.playing ? "Pause" : seq.step === 3 ? "Run again ↻" : "Pay →"}
        </button>
        <button onClick={seq.next} disabled={!!error || seq.step === 3}>
          Step
        </button>
        <button onClick={seq.reset}>Reset</button>
        <span>{seq.step + 1} / 4</span>
        <small>Local interactive model · no payment sent</small>
      </div>
      <p
        className={`lab-caption ${error || (seq.step === 3 && wrong) ? "bad-text" : ""}`}
        aria-live="polite"
      >
        {error || describe[seq.step]}
      </p>
      <div className="try-note">
        Try this: switch to INR, compare truncation with rounding, then try JPY.
        Which mistake does rounding actually fix?
      </div>
    </div>
  );
}
