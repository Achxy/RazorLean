/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */

import React from "react";
import ReactDOM from "react-dom/client";
import { BladeProvider } from "@razorpay/blade/components";
import { bladeTheme } from "@razorpay/blade/tokens";
import "@razorpay/blade/fonts.css";
import "./styles.css";
import { App } from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode><BladeProvider themeTokens={bladeTheme} colorScheme="light"><App /></BladeProvider></React.StrictMode>,
);
