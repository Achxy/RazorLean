/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { useEffect, useState } from "react";

const mcpCommit = "7950d51d118ca164c32b7cf0cfaa14f34f24849f";
export const sourceSnippets = {
  checkout: {
    repo: "razorpay-mcp-server",
    commit: mcpCommit,
    path: "pkg/razorpay/integrations/frontend_templates.go",
    start: 41,
    end: 45,
    highlight: 44,
    title: "The browser supplies the order amount",
  },
  ascii: {
    repo: "razorpay-dot-net",
    commit: "2cd38a155ec56ea47e879a573a3acb19334c152e",
    path: "src/Utils.cs",
    start: 133,
    end: 137,
    highlight: 135,
    title: "The verifier re-encodes text as ASCII",
  },
  mobile: {
    repo: "razorpay-mcp-server",
    commit: mcpCommit,
    path: "pkg/razorpay/integrations/mobile.go",
    start: 404,
    end: 409,
    highlight: 407,
    title: "The generated callback forwards an empty signature",
  },
} as const;

export function GitHubSnippet({
  source,
}: {
  source: keyof typeof sourceSnippets;
}) {
  const spec = sourceSnippets[source];
  const [lines, setLines] = useState<string[] | null>(null);
  const [failed, setFailed] = useState(false);
  const url = `https://github.com/razorpay/${spec.repo}/blob/${spec.commit}/${spec.path}`;
  useEffect(() => {
    const controller = new AbortController();
    setLines(null);
    setFailed(false);
    fetch(
      `https://raw.githubusercontent.com/razorpay/${spec.repo}/${spec.commit}/${spec.path}`,
      { signal: controller.signal },
    )
      .then((response) => {
        if (!response.ok) throw new Error("Source unavailable");
        return response.text();
      })
      .then((text) => {
        const all = text.split("\n");
        if (all.length < spec.end) throw new Error("Source range unavailable");
        if (!controller.signal.aborted)
          setLines(all.slice(spec.start - 1, spec.end));
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailed(true);
      });
    return () => controller.abort();
  }, [spec]);
  const indent = lines
    ? Math.min(
        ...lines
          .filter((line) => line.trim())
          .map((line) => line.match(/^\s*/)?.[0].length ?? 0),
      )
    : 0;
  return (
    <figure className="github-snippet">
      <figcaption>
        <strong>{spec.title}</strong>
        <a
          href={`${url}#L${spec.start}-L${spec.end}`}
          target="_blank"
          rel="noreferrer"
        >
          razorpay/{spec.repo} ↗
        </a>
        <span>{spec.path}</span>
      </figcaption>
      {lines ? (
        <div
          className="github-code-scroll"
          tabIndex={0}
          role="region"
          aria-label={`${spec.title}: source code`}
        >
          <pre>
            <code>
              {lines.map((line, index) => {
                const number = spec.start + index;
                return (
                  <span
                    className={`github-code-line ${number === spec.highlight ? "source-highlight" : ""}`}
                    key={number}
                  >
                    <a
                      className="source-line-number"
                      href={`${url}#L${number}`}
                      aria-label={`Open line ${number} on GitHub`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {number}
                    </a>
                    <span>{line.slice(indent) || " "}</span>
                    {"\n"}
                  </span>
                );
              })}
            </code>
          </pre>
        </div>
      ) : (
        <p role="status">
          {failed
            ? "GitHub source could not be loaded. Open the repository link above to inspect it."
            : "Loading source from GitHub…"}
        </p>
      )}
      <footer>
        Pinned source ·{" "}
        <a
          href={`https://github.com/razorpay/${spec.repo}/commit/${spec.commit}`}
          target="_blank"
          rel="noreferrer"
        >
          commit {spec.commit.slice(0, 7)}
        </a>{" "}
        · lines {spec.start}–{spec.end}
      </footer>
    </figure>
  );
}
