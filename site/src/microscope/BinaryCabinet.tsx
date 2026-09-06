/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { useState } from "react";
import type { PriceInspection } from "./binary64";

export function BinaryCabinet({ model }: { model: PriceInspection }) {
  const [which, setWhich] = useState<"input" | "product">("input");
  const [field, setField] = useState("fraction");
  const number = model[which];
  return (
    <div className="binary-cabinet">
      <div
        className="instrument-tabs"
        role="group"
        aria-label="Inspect a stored number"
      >
        <button
          aria-pressed={which === "input"}
          onClick={() => setWhich("input")}
        >
          The stored price
        </button>
        <button
          aria-pressed={which === "product"}
          onClick={() => setWhich("product")}
        >
          After × 100
        </button>
      </div>
      <div className="decimal-specimen">
        <span>Exact value of these 64 bits</span>
        <output data-testid="exact-binary-value">
          {which === "input" ? model.exactInput : model.exactProduct}
        </output>
      </div>
      <div className="bit-ribbon" aria-hidden="true">
        {number.bits.split("").map((bit, i) => {
          const kind = i === 0 ? "sign" : i < 12 ? "exponent" : "fraction";
          return (
            <span
              key={i}
              className={`bit bit-${kind} ${bit === "1" ? "bit-on" : ""} ${kind === field ? "bit-selected" : ""}`}
            >
              {bit}
            </span>
          );
        })}
      </div>
      <div
        className="bit-key"
        role="group"
        aria-label="Inspect a binary64 field"
      >
        {["sign", "exponent", "fraction"].map((name, i) => (
          <button
            key={name}
            className={`key-${name}`}
            onClick={() => setField(name)}
            aria-pressed={field === name}
          >
            {["1 sign bit", "11 exponent bits", "52 fraction bits"][i]}
          </button>
        ))}
      </div>
      <p className="bit-explanation" aria-live="polite">
        {field === "sign"
          ? "The first bit is zero: this is a positive number. It is not the source of the lost paise."
          : field === "exponent"
            ? `The exponent scales the significand by 2 to the power ${number.exponent}. A fixed number of fraction bits means the spacing between representable values changes with magnitude.`
            : "Each position contributes a power of one half. A finite row can store 1/2 or 1/4 exactly. It cannot store every fraction with a denominator of 100 exactly."}
      </p>
    </div>
  );
}
