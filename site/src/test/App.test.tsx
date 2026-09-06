/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import {
  act,
  cleanup,
  fireEvent,
  render,
  renderHook,
} from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { PaymentLab } from "../components/PaymentLab";
import { BoundaryLab } from "../components/BoundaryLab";
import { useSequence } from "../components/useSequence";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

test("pause cancels progression and reset cancels a running sequence", () => {
  vi.useFakeTimers();
  const { result } = renderHook(() => useSequence(3, 1000));
  act(() => result.current.toggle());
  act(() => vi.advanceTimersByTime(1000));
  expect(result.current.step).toBe(1);
  act(() => result.current.toggle());
  act(() => vi.advanceTimersByTime(5000));
  expect(result.current.step).toBe(1);
  act(() => result.current.toggle());
  act(() => result.current.reset());
  act(() => vi.advanceTimersByTime(5000));
  expect(result.current.step).toBe(0);
  expect(result.current.playing).toBe(false);
});

test("a reader can change the conversion and rerun a corrected order", () => {
  const view = render(<PaymentLab />);
  for (let i = 0; i < 3; i++)
    fireEvent.click(view.getByRole("button", { name: "Step" }));
  expect(
    view.getByText(/changed the order by 29205 subunits/),
  ).toBeInTheDocument();
  fireEvent.change(view.getByLabelText("Conversion block"), {
    target: { value: "exact" },
  });
  for (let i = 0; i < 3; i++)
    fireEvent.click(view.getByRole("button", { name: "Step" }));
  expect(view.getByText(/outgoing integer preserves Bob/)).toBeInTheDocument();
  fireEvent.change(view.getByLabelText("Bob’s price"), {
    target: { value: "0.5" },
  });
  expect(view.getByRole("button", { name: "Pay →" })).toBeDisabled();
});

test("keyboard block moves repair both ordering errors", () => {
  const view = render(<BoundaryLab />);
  fireEvent.click(view.getByRole("button", { name: "Step" }));
  expect(view.getByText(/decoding before authentication/)).toBeInTheDocument();
  fireEvent.click(
    view.getByRole("button", { name: "Move Verify original bytes up" }),
  );
  fireEvent.click(
    view.getByRole("button", { name: "Move Match Bob’s quote up" }),
  );
  for (let i = 0; i < 4; i++)
    fireEvent.click(view.getByRole("button", { name: "Step" }));
  expect(view.getByText("Fulfillment permitted")).toBeInTheDocument();
});
