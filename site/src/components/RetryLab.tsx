/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { retrySnapshot } from "./payment-model";
import { useSequence } from "./useSequence";

const captions = [
  "Bob owes Alice a refund. One intention, one effect.",
  "Bob sends the refund request. The response has not arrived yet.",
  "The provider commits the refund. Alice’s balance changes; Bob still has no response.",
  "The response is lost. Bob cannot distinguish ‘not processed’ from ‘processed, acknowledgement lost’.",
  "Bob retries. Watch what happens when the logical identity is preserved or replaced.",
  "The second request reaches the effect boundary.",
  "The response arrives. Compare request count with economic effect count.",
];

export function RetryLab() {
  const [stable, setStable] = useState(false);
  const seq = useSequence(6, 1400);
  const reduced = useReducedMotion();
  const state = retrySnapshot(seq.step, stable);
  const packet = [
    [90, 60],
    [590, 60],
    [590, 105],
    [340, 150],
    [590, 205],
    [590, 250],
    [90, 290],
  ][seq.step];
  return (
    <div className="lab retry-lab">
      <label className="toggle-line">
        <input
          type="checkbox"
          checked={stable}
          onChange={(e) => {
            setStable(e.target.checked);
            seq.reset();
          }}
        />
        Preserve one durable effect identity across the retry
      </label>
      <div className="retry-stage">
        <svg
          viewBox="0 0 680 335"
          role="img"
          aria-label={`Refund timeline. ${captions[seq.step]} ${state.effects} effects.`}
        >
          <text x="90" y="25" textAnchor="middle">
            Bob’s server
          </text>
          <text x="590" y="25" textAnchor="middle">
            Effect boundary
          </text>
          <path
            d="M90 45V310M590 45V310"
            stroke="#47473f"
            strokeDasharray="3 7"
          />
          {[
            { d: "M90 60H590", at: 1, label: "request", x: 340, y: 49 },
            {
              d: "M590 150H340",
              at: 3,
              label: "acknowledgement lost ×",
              x: 410,
              y: 139,
            },
            {
              d: "M90 205H590",
              at: 4,
              label: stable ? "retry · same intent" : "retry · new intent",
              x: 340,
              y: 194,
            },
            {
              d: "M590 290H90",
              at: 6,
              label: "acknowledgement",
              x: 340,
              y: 279,
            },
          ].map((row) => (
            <g key={row.at}>
              <motion.path
                d={row.d}
                stroke={row.at === 3 ? "#dd745f" : "#81a981"}
                strokeWidth="2"
                initial={false}
                animate={{
                  pathLength: seq.step >= row.at ? 1 : 0,
                  opacity: seq.step >= row.at ? 1 : 0.15,
                }}
                transition={{ duration: reduced ? 0 : 0.7 }}
              />
              <text
                x={row.x}
                y={row.y}
                textAnchor="middle"
                opacity={seq.step >= row.at ? 1 : 0.25}
              >
                {row.label}
              </text>
            </g>
          ))}
          <motion.circle
            r="6"
            fill="#e8ca91"
            initial={false}
            animate={{ cx: packet[0], cy: packet[1] }}
            transition={{ duration: reduced ? 0 : 0.7 }}
          />
          {seq.step >= 2 && (
            <text x="576" y="113" textAnchor="end" className="good-text">
              refund committed
            </text>
          )}
          {seq.step >= 5 && (
            <text
              x="576"
              y="258"
              textAnchor="end"
              className={stable ? "good-text" : "bad-text"}
            >
              {stable ? "replay stored result" : "second refund committed"}
            </text>
          )}
        </svg>
        <div className="effect-counter">
          <span>Network requests</span>
          <b>{state.requests}</b>
          <span>Refund effects</span>
          <motion.b
            key={state.effects}
            initial={{ opacity: 0.3 }}
            animate={{ opacity: 1 }}
            className={state.effects > 1 ? "bad-text" : "good-text"}
          >
            {state.effects}
          </motion.b>
          <small>
            {state.known
              ? "Bob knows the result."
              : seq.step >= 2
                ? "Committed ≠ acknowledged."
                : "Nothing sent yet."}
          </small>
        </div>
      </div>
      <div className="transport">
        <button className="run" onClick={seq.toggle}>
          {seq.playing
            ? "Pause"
            : seq.step === 6
              ? "Replay ↻"
              : "Send refund →"}
        </button>
        <button onClick={seq.next} disabled={seq.step === 6}>
          Step
        </button>
        <button onClick={seq.reset}>Reset</button>
        <span>{seq.step} / 6</span>
      </div>
      <p className="lab-caption" aria-live="polite">
        {captions[seq.step]}{" "}
        {seq.step >= 5 &&
          (stable
            ? "The durable record returns the first outcome without another effect."
            : "In this model, the retry has a new identity, so a second valid request creates a second effect.")}
      </p>
      <p className="try-note">
        This models an idempotency contract, not a universal Razorpay defect.
        Distinct requests may intentionally create distinct effects. Ambiguous
        writes require reconciliation; a local key alone does not make an
        external provider write exactly-once.
      </p>
    </div>
  );
}
