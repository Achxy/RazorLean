/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { useEffect, useRef } from "react";
import { animate, useReducedMotion } from "motion/react";
import type { GuideCase } from "./cases";
import { paintPlate, PLATE_HEIGHT, PLATE_WIDTH } from "./plate-renderer";

export function Plate({ item, step }: { item: GuideCase; step: number }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const reduced = useReducedMotion();
  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    const context = element.getContext("2d");
    if (!context) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    element.width = PLATE_WIDTH * dpr;
    element.height = PLATE_HEIGHT * dpr;
    context.scale(dpr, dpr);
    const draw = (progress: number) => {
      const report = paintPlate(context, item, step, progress);
      element.dataset.layoutOverlaps = JSON.stringify(report.overlaps);
      element.dataset.layoutOutside = JSON.stringify(report.outside);
    };
    draw(1);
    const controls = reduced
      ? undefined
      : animate(0, 1, { duration: 0.65, ease: "easeInOut", onUpdate: draw });
    let mounted = true;
    void document.fonts.ready.then(() => {
      if (mounted) draw(1);
    });
    return () => {
      mounted = false;
      controls?.stop();
    };
  }, [item, step, reduced]);
  return (
    <div
      className="plate-scroll"
      tabIndex={0}
      role="region"
      aria-label="Illustration; scroll horizontally on narrow screens"
    >
      <canvas
        ref={canvas}
        className="guide-plate"
        role="img"
        aria-label={`${item.title}. ${item.frames[step]}`}
      />
    </div>
  );
}
