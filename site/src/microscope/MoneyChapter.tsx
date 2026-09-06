/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { useMemo, useState } from "react";
import { inspectPrice, priceFromPaise, microscopeView } from "./binary64";
import { Ruler } from "./Ruler";
import { BinaryCabinet } from "./BinaryCabinet";
import { ConversionBench, UnitBench } from "./ConversionBench";
import { GitHubSnippet } from "../components/GitHubSnippet";
import { findings } from "../data/evidence";
import { excerptFor } from "../field-guide/source-excerpt";
import "./microscope.css";

const pinnedSource = excerptFor(
  findings.find((f) => f.id === "RP-MCP-GENERATOR-MONEY-UNDERCHARGE")!,
);
// This range is Python embedded inside the generator's Go source string.
const source = pinnedSource ? { ...pinnedSource, language: "python" } : null;

export function MoneyChapter() {
  const [price, setPrice] = useState("2.01");
  const [zoom, setZoom] = useState(0);
  const [bitsOpen, setBitsOpen] = useState(false);
  const [sourceOpen, setSourceOpen] = useState(false);
  const inspection = useMemo(() => {
    try {
      return { model: inspectPrice(price), error: "" };
    } catch (error) {
      return { model: null, error: (error as Error).message };
    }
  }, [price]);
  const model = inspection.model;
  const zoomText = model
    ? microscopeView(model, zoom, 800).magnification.toLocaleString("en-US", {
        maximumFractionDigits: 0,
      })
    : "1";
  return (
    <div className="money-chapter" id="microscope">
      <div className="chapter-opening">
        <p className="chapter-eyebrow">ONE PAYMENT, TAKEN APART</p>
        <h1>The price was ₹2.01.</h1>
        <p>
          Alice agrees to pay Bob two rupees and one paise. His integration
          multiplies the price by 100, then turns it into an integer. That
          sounds reasonable. It produces <em>200</em>.
        </p>
        <p>Before blaming the payment API, let’s open up the number.</p>
      </div>
      <div className="microscope-instrument">
        <div className="price-controls">
          <label>
            Bob’s price{" "}
            <span className="price-input">
              <span aria-hidden="true">₹</span>
              <input
                aria-label="Price under the microscope"
                inputMode="decimal"
                value={price}
                maxLength={7}
                onChange={(event) => setPrice(event.target.value)}
                aria-invalid={!!inspection.error}
                aria-describedby={inspection.error ? "price-error" : undefined}
              />
            </span>
          </label>
          <div className="price-presets">
            <span>Compare a neighbour or an exact fraction</span>
            {["2.01", "2.02", "2.50"].map((p) => (
              <button
                key={p}
                aria-pressed={price === p}
                onClick={() => setPrice(p)}
              >
                ₹{p}
              </button>
            ))}
          </div>
        </div>
        <label className="price-scrubber">
          Or scrub prices from ₹1 to ₹3
          <input
            type="range"
            min={100}
            max={300}
            step={1}
            value={
              model ? Math.max(100, Math.min(300, Number(model.intended))) : 201
            }
            onChange={(event) =>
              setPrice(priceFromPaise(Number(event.target.value)))
            }
            aria-label="Scrub price in paise"
            aria-valuetext={model ? `₹${price}` : "Invalid price"}
          />
        </label>
        {model ? (
          <>
            <Ruler model={model} zoom={zoom} onZoom={setZoom} />
            <div className="zoom-control">
              <label htmlFor="money-zoom">
                Magnification <output>{zoomText}×</output>
              </label>
              <input
                id="money-zoom"
                type="range"
                min={0}
                max={1}
                step={0.001}
                value={zoom}
                onChange={(event) => setZoom(Number(event.target.value))}
                aria-valuetext={`${zoomText} times`}
              />
              <div>
                <button onClick={() => setZoom(0)}>Ordinary scale</button>
                <button onClick={() => setZoom(1)}>Resolve the last bit</button>
              </div>
            </div>
            <p className="microscope-observation" aria-live="polite">
              {model.error.numerator === 0n
                ? `For ₹${price}, the product lands exactly on ${model.intended}. Not every price fails.`
                : zoom < 0.8
                  ? "The two marks appear to coincide. Magnify the ruler: a difference too small to see can still decide which integer survives."
                  : `The stored product sits ${model.error.numerator < 0n ? "below" : "above"} ${model.intended}. The gap is tiny. An integer conversion does not care how tiny.`}
            </p>
          </>
        ) : (
          <p id="price-error" role="alert" className="price-error">
            {inspection.error}
          </p>
        )}
        <p className="instrument-note">
          Live browser arithmetic, not recorded frames. The ruler’s distance
          scale is logarithmically adjustable; values are not moved to
          exaggerate the error.
        </p>
      </div>
      <div className="chapter-prose">
        <h2>The number on the tag is not the number in memory.</h2>
        <p>
          Decimals divide a unit into tenths and hundredths. Binary fractions
          divide it into halves, quarters and eighths. Some values fit both
          systems exactly. Many prices don’t.
        </p>
        <p>
          The computer stores the nearest available binary value. Multiplication
          rounds to another available value. That is normal floating-point
          behaviour. The mistake is treating the resulting approximation as
          exact money.
        </p>
      </div>
      <details
        className="binary-disclosure"
        onToggle={(event) => setBitsOpen(event.currentTarget.open)}
      >
        <summary>
          Open the 64-bit representation <span>the actual bits, decoded</span>
        </summary>
        {bitsOpen && model && <BinaryCabinet model={model} />}
        <p className="instrument-note">
          Decoded with DataView; exact fractions and decimal expansions use
          BigInt.{" "}
          <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number#number_encoding">
            About binary64 ↗
          </a>
        </p>
      </details>
      <div className="chapter-prose">
        <h2>Now throw away the fraction.</h2>
        <p>
          An integer conversion is a boundary, not a tolerance check. A value
          just below 201 becomes 200 when its fraction is discarded. Use the
          same price and change only that final operation.
        </p>
      </div>
      {model ? (
        <ConversionBench model={model} />
      ) : (
        <p className="price-error">
          Enter a valid price above to inspect the conversion.
        </p>
      )}
      <div className="chapter-prose">
        <h2>Rounding helps. But which unit are we rounding to?</h2>
        <p>
          Bob adds a Japanese price. A yen is already the smallest unit.
          Multiplying it by 100 is no longer a tiny numerical error: it changes
          the order’s meaning by a factor of 100.
        </p>
      </div>
      <UnitBench />
      <div className="chapter-prose">
        <h2>The repair belongs before the request.</h2>
        <p>
          Keep the agreed price as decimal digits. Apply the currency’s unit
          rules. Reject an amount that cannot be represented, and only then
          create the integer request. That is the{" "}
          <a href="https://github.com/Achxy/RazorLean/blob/main/razorproof-rs/crates/razorproof-core/src/money.rs#L151">
            money boundary RazorProof implements in Rust
          </a>
          .
        </p>
        <p>
          The browser instruments above compute the arithmetic independently;
          they are not a Rust runtime or a provider test. The source below
          connects the failure to the official integration generator.
        </p>
      </div>
      <details
        className="microscope-source"
        onToggle={(event) => setSourceOpen(event.currentTarget.open)}
      >
        <summary>Where this enters the generated integration</summary>
        {sourceOpen && source && <GitHubSnippet excerpt={source} />}
        <p>
          The pinned templates and recorded investigation cover seven generated
          backends. This chapter computes one binary64 mechanism, not seven
          language runtimes.
        </p>
      </details>
      <p className="chapter-credit">
        Interaction approach inspired by{" "}
        <a href="https://ciechanow.ski/mechanical-watch/">
          Bartosz Ciechanowski’s Mechanical Watch
        </a>
        . Original drawings and implementation.
      </p>
    </div>
  );
}
