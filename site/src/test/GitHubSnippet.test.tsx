/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { cleanup, render } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { GitHubSnippet } from "../components/GitHubSnippet";
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
test("renders fetched lines with upstream commit-pinned anchors", async () => {
  const lines = Array.from(
    { length: 137 },
    (_, i) => `    original line ${i + 1}`,
  );
  lines[134] = "    var encoding = new ASCIIEncoding();";
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, text: async () => lines.join("\n") }),
  );
  const view = render(<GitHubSnippet source="ascii" />);
  expect(await view.findByRole("region")).toHaveTextContent(
    "var encoding = new ASCIIEncoding();",
  );
  expect(view.container.querySelector(".hljs-keyword")).not.toBeNull();
  expect(
    view.getByRole("link", { name: "Open line 135 on GitHub" }),
  ).toHaveAttribute(
    "href",
    "https://github.com/razorpay/razorpay-dot-net/blob/2cd38a155ec56ea47e879a573a3acb19334c152e/src/Utils.cs#L135",
  );
  expect(view.queryByText("original line 132")).not.toBeInTheDocument();
  expect(view.getAllByRole("link", { name: /Open line/ })).toHaveLength(5);
});
test("keeps the upstream link usable when fetching fails", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
  const view = render(<GitHubSnippet source="mobile" />);
  expect(await view.findByText(/could not be loaded/)).toBeInTheDocument();
  expect(
    view.getByRole("link", { name: /razorpay\/razorpay-mcp-server/ }),
  ).toHaveAttribute("href", expect.stringContaining("#L404-L409"));
});
