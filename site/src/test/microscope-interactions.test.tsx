/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { MoneyChapter } from "../microscope/MoneyChapter";
vi.mock("../microscope/Ruler", () => ({
  Ruler: () => <div aria-label="Canvas rendering tested separately" />,
}));
afterEach(cleanup);
test("the same price drives the output, and repairs do not need prewritten frames", () => {
  const view = render(<MoneyChapter />);
  expect(view.getByTestId("conversion-result")).toHaveTextContent("200paise");
  fireEvent.click(view.getByRole("button", { name: "Round to nearest" }));
  expect(view.getByTestId("conversion-result")).toHaveTextContent("201paise");
  fireEvent.change(view.getByLabelText("Price under the microscope"), {
    target: { value: "3.51" },
  });
  expect(view.getByTestId("conversion-result")).toHaveTextContent("351paise");
  fireEvent.click(view.getByRole("button", { name: "Discard the fraction" }));
  expect(view.getByTestId("conversion-result")).toHaveTextContent(
    String(Math.trunc(3.51 * 100)),
  );
  fireEvent.click(view.getByRole("button", { name: "Keep decimal intent" }));
  expect(view.getByTestId("conversion-result")).toHaveTextContent("351paise");
});
test("invalid prices remove stale calculations and can recover", () => {
  const view = render(<MoneyChapter />);
  fireEvent.change(view.getByLabelText("Price under the microscope"), {
    target: { value: "2.001" },
  });
  expect(view.getByRole("alert")).toHaveTextContent(
    "at most two decimal places",
  );
  expect(view.queryByTestId("conversion-result")).toBeNull();
  fireEvent.change(view.getByLabelText("Price under the microscope"), {
    target: { value: "2.50" },
  });
  expect(view.queryByRole("alert")).toBeNull();
  expect(view.getByTestId("conversion-result")).toHaveTextContent("250paise");
});
test("currency choice changes the unit contract, not just the currency label", () => {
  const view = render(<MoneyChapter />);
  expect(view.getByTestId("unit-result")).toHaveTextContent("29500yen");
  fireEvent.click(view.getByLabelText("Let the currency choose the unit"));
  expect(view.getByTestId("unit-result")).toHaveTextContent("295yen");
  fireEvent.click(view.getByRole("button", { name: "KWD" }));
  expect(view.getByTestId("unit-result")).toHaveTextContent("295990fils");
});
