/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { render } from "@testing-library/react";
import { expect, test } from "vitest";
import { BladeProvider } from "@razorpay/blade/components";
import { bladeTheme } from "@razorpay/blade/tokens";
import { App } from "../App";

test("opens with the economic-integrity counterexample", () => {
  const view = render(<BladeProvider themeTokens={bladeTheme}><App /></BladeProvider>);
  expect(view.getByRole("heading", { name: /valid signature/i })).toBeInTheDocument();
  expect(view.getByText(/Alice enters ¥295/i)).toBeInTheDocument();
  expect(view.getByRole("heading", { name: /No pooled score/i })).toBeInTheDocument();
});
