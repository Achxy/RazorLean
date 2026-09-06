/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import type { Finding } from "../data/evidence";
import type { SourceExcerpt } from "../components/GitHubSnippet";

export function excerptFor(finding: Finding): SourceExcerpt | null {
  for (const evidence of finding.evidence) {
    const match = evidence.source_url.match(
      /^https:\/\/github\.com\/razorpay\/([^/]+)\/blob\/([a-f0-9]{40})\/([^#]+)(?:#.*)?$/,
    );
    if (!match || !evidence.line || evidence.line < 1) continue;
    const path = match[3];
    const extension = path.split(".").pop() || "";
    const language: Record<string, string> = {
      go: "go",
      cs: "csharp",
      java: "java",
      py: "python",
      rb: "ruby",
      js: "javascript",
      php: "php",
    };
    return {
      repo: match[1],
      commit: match[2],
      path,
      start: Math.max(1, evidence.line - 2),
      end: evidence.line + 2,
      highlight: evidence.line,
      title: evidence.summary,
      language: language[extension] || "plaintext",
    };
  }
  return null;
}
