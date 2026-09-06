/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { useEffect, useState } from "react";

export function useSequence(last: number, interval = 1300) {
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    if (!playing) return;
    if (step >= last) {
      setPlaying(false);
      return;
    }
    const id = window.setTimeout(
      () => setStep((value) => Math.min(last, value + 1)),
      interval,
    );
    return () => window.clearTimeout(id);
  }, [playing, step, last, interval]);
  return {
    step,
    playing,
    setStep,
    reset: () => {
      setPlaying(false);
      setStep(0);
    },
    next: () => {
      setPlaying(false);
      setStep((value) => Math.min(last, value + 1));
    },
    toggle: () => {
      if (step >= last) setStep(0);
      setPlaying((value) => !value);
    },
  };
}
