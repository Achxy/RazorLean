/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { render } from "@testing-library/react";
import { expect, test } from "vitest";
import { App } from "../App";

test("opens with the economic-integrity counterexample", () => {
  const view = render(<App />);
  expect(view.getByRole("heading", { name: /How a payment can be/i })).toBeInTheDocument();
  expect(view.getByText(/Alice wants an item/i)).toBeInTheDocument();
  expect(view.getByRole("heading", { name: /entire failure notebook/i })).toBeInTheDocument();
});
