/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */
import { useEffect, useRef, type PointerEvent } from "react";
import { animate, useMotionValue, useReducedMotion } from "motion/react";
import type { PriceInspection } from "./binary64";
import { drawRuler, RULER_HEIGHT } from "./draw-ruler";

export function Ruler({
  model,
  zoom,
  onZoom,
}: {
  model: PriceInspection;
  zoom: number;
  onZoom: (zoom: number) => void;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const position = useMotionValue(zoom);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (reduced) {
      position.set(zoom);
      return;
    }
    const control = animate(position, zoom, {
      duration: 0.18,
      ease: [0.22, 1, 0.36, 1],
    });
    return () => control.stop();
  }, [zoom, position, reduced]);
  useEffect(() => {
    const element = canvas.current;
    if (!element) return;
    const ctx = element.getContext("2d");
    if (!ctx) return;
    let width = element.clientWidth;
    let pending = 0,
      active = true;
    const draw = () => {
      pending = 0;
      const dpr = Math.min(devicePixelRatio || 1, 2);
      if (element.width !== Math.round(width * dpr))
        element.width = Math.round(width * dpr);
      if (element.height !== RULER_HEIGHT * dpr)
        element.height = RULER_HEIGHT * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const report = drawRuler(ctx, model, position.get(), width);
      element.dataset.layoutOutside = JSON.stringify(report.outside);
      element.dataset.layoutOverlaps = JSON.stringify(report.overlaps);
      element.dataset.actualX = String(report.actualX);
      element.dataset.targetX = String(report.center);
    };
    const schedule = () => {
      if (!pending) pending = requestAnimationFrame(draw);
    };
    const unsubscribe = position.on("change", schedule);
    const observer = new ResizeObserver((entries) => {
      width = entries[0].contentRect.width;
      schedule();
    });
    observer.observe(element);
    void document.fonts.ready.then(() => {
      if (active) schedule();
    });
    draw();
    return () => {
      active = false;
      observer.disconnect();
      unsubscribe();
      cancelAnimationFrame(pending);
    };
  }, [model, position]);
  const move = (event: PointerEvent<HTMLCanvasElement>) => {
    const rect = event.currentTarget.getBoundingClientRect();
    onZoom(Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width)));
  };
  return (
    <canvas
      className="numerical-ruler"
      ref={canvas}
      role="img"
      aria-label={`Numerical microscope. Intended ${model.intended} paise. Stored product ${model.exactProduct}. Use the magnification slider to inspect the difference.`}
      onPointerDown={(event) => {
        event.currentTarget.setPointerCapture(event.pointerId);
        move(event);
      }}
      onPointerMove={(event) => {
        if (event.currentTarget.hasPointerCapture(event.pointerId)) move(event);
      }}
      onPointerUp={(event) =>
        event.currentTarget.releasePointerCapture(event.pointerId)
      }
    />
  );
}
