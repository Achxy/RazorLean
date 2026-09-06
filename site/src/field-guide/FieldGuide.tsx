/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { useMemo, useState } from "react";
import { findings, claimLabel, gradeLabel } from "../data/evidence";
import { guideCases } from "./cases";
import type { GuideCase } from "./cases";
import { Plate } from "./Plate";
import { useSequence } from "../components/useSequence";
import { GitHubSnippet } from "../components/GitHubSnippet";
import { excerptFor } from "./source-excerpt";
import "./field-guide.css";

function CaseStudy({
  item,
  index,
  onSelect,
}: {
  item: GuideCase;
  index: number;
  onSelect: (id: string) => void;
}) {
  const sequence = useSequence(3, 3300);
  const [sourceOpen, setSourceOpen] = useState(false);
  const finding = findings.find((f) => f.id === item.id)!;
  const excerpt = useMemo(() => excerptFor(finding), [finding]);
  const sources = finding.evidence.filter(
    (e) => e.source_url && e.source_url.includes("github.com/"),
  );
  return (
    <article className="case-study" id="case-study" aria-label={item.title}>
      <div className="case-kicker">
        <span>
          Plate {String(index + 1).padStart(2, "0")} / {guideCases.length}
        </span>
        <span>
          {item.group} · {finding.repo}
        </span>
      </div>
      <h3>{item.title}</h3>
      <p className="case-story">{item.story}</p>
      <figure className="case-illustration">
        <Plate item={item} step={sequence.step} />
        <figcaption>
          <span>
            {
              [
                "The intention",
                "The translation",
                "The failure",
                "The corrected contract",
              ][sequence.step]
            }
          </span>
          <p aria-live="polite">{item.frames[sequence.step]}</p>
        </figcaption>
      </figure>
      <div className="plate-controls">
        <button onClick={sequence.toggle} className="plate-play">
          {sequence.playing
            ? "Pause"
            : sequence.step === 3
              ? "Replay the mechanism"
              : "Play the mechanism"}
        </button>
        <div
          className="plate-steps"
          role="group"
          aria-label="Illustration stage"
        >
          {["Intention", "Translation", "Failure", "Correction"].map(
            (label, i) => (
              <button
                key={label}
                aria-pressed={sequence.step === i}
                onClick={() => {
                  sequence.reset();
                  sequence.setStep(i);
                }}
              >
                {i + 1}
                <span>{label}</span>
              </button>
            ),
          )}
        </div>
      </div>
      <div className="case-explanation">
        <div>
          <h4>Where it changes</h4>
          <p>{item.mechanism}</p>
          <h4>Why it matters</h4>
          <p>{item.consequence}</p>
        </div>
        <div>
          <h4>The repair</h4>
          <p>{item.repair}</p>
          <div className="evidence-bound">
            <h4>What the evidence establishes</h4>
            <p>{item.scope}</p>
            <small>
              {claimLabel[finding.claim_kind] ?? finding.claim_kind} ·{" "}
              {gradeLabel[finding.level] ?? finding.level}
            </small>
          </div>
        </div>
      </div>
      <details
        className="case-source"
        onToggle={(event) => setSourceOpen(event.currentTarget.open)}
      >
        <summary>Inspect the source behind this plate</summary>
        <p>{finding.title}</p>
        {sourceOpen && excerpt && <GitHubSnippet excerpt={excerpt} />}
        <div className="case-source-links">
          {sources.map((source, i) => (
            <a
              key={i}
              href={
                source.line && source.source_url.includes("/blob/")
                  ? `${source.source_url.split("#")[0]}#L${source.line}`
                  : source.source_url
              }
              target="_blank"
              rel="noreferrer"
            >
              {source.summary} ↗
            </a>
          ))}
        </div>
        <p className="case-enforcement">
          The correction is a required contract, not a claim that an upstream
          SDK has been patched. RazorProof can enforce its own boundaries; SDK,
          generator and documentation repairs require changes in those
          components.
        </p>
      </details>
      <nav className="case-pagination" aria-label="Read adjacent case">
        <button
          disabled={index === 0}
          onClick={() => onSelect(guideCases[index - 1].id)}
        >
          ← Previous plate
        </button>
        <button
          disabled={index === guideCases.length - 1}
          onClick={() => onSelect(guideCases[index + 1].id)}
        >
          Next: {guideCases[index + 1]?.title ?? "End of field guide"} →
        </button>
      </nav>
    </article>
  );
}

export function FieldGuide() {
  const [selected, setSelected] = useState(guideCases[0].id);
  const [query, setQuery] = useState("");
  const [group, setGroup] = useState("All");
  const filtered = useMemo(
    () =>
      guideCases.filter(
        (item) =>
          (group === "All" || item.group === group) &&
          `${item.title} ${item.story} ${item.mechanism} ${item.repair} ${item.plate} ${item.id} ${findings.find((f) => f.id === item.id)?.repo}`
            .toLowerCase()
            .includes(query.toLowerCase()),
      ),
    [group, query],
  );
  const selectCase = (id: string) => {
    setSelected(id);
    requestAnimationFrame(() =>
      document
        .getElementById("case-study")
        ?.scrollIntoView({ block: "start", behavior: "instant" }),
    );
  };
  const index = guideCases.findIndex((item) => item.id === selected);
  return (
    <div className="field-guide" id="cases">
      <aside
        className="guide-directory"
        aria-label="Illustrated case directory"
      >
        <label>
          Find a mechanism
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="refund, encoding, tenant…"
          />
        </label>
        <label>
          Chapter
          <select value={group} onChange={(e) => setGroup(e.target.value)}>
            {["All", "Money", "Authenticity", "Identity", "Integration"].map(
              (g) => (
                <option key={g}>{g}</option>
              ),
            )}
          </select>
        </label>
        <div className="guide-case-list">
          {filtered.map((item) => (
            <button
              key={item.id}
              aria-pressed={selected === item.id}
              aria-controls="case-study"
              onClick={() => selectCase(item.id)}
            >
              <span>
                {String(guideCases.indexOf(item) + 1).padStart(2, "0")}
              </span>
              <b>{item.title}</b>
            </button>
          ))}
          {!filtered.length && <p>No matching plate. Try a broader term.</p>}
        </div>
      </aside>
      <CaseStudy
        key={selected}
        item={guideCases[index]}
        index={index}
        onSelect={selectCase}
      />
    </div>
  );
}
