/*
 * Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
 * SPDX-License-Identifier: MIT
 * Licensed under the MIT License. See LICENSE in the repository root.
 */

import { useEffect, useRef } from "react";
import rough from "roughjs";

export function RoughMark({ kind = "circle" }: { kind?: "circle" | "underline" }) {
  const ref = useRef<SVGSVGElement>(null);
  useEffect(() => {
    const svg = ref.current;
    if (!svg) return;
    svg.replaceChildren();
    const rc = rough.svg(svg);
    const node = kind === "circle"
      ? rc.ellipse(102, 42, 194, 72, { seed: 41, stroke: "#ff5f3d", strokeWidth: 2.2, roughness: 0.75, fill: "none" })
      : rc.path("M 4 28 C 62 23, 138 33, 200 25", { seed: 17, stroke: "#0648ef", strokeWidth: 2.4, roughness: 0.8 });
    svg.appendChild(node);
  }, [kind]);
  return <svg ref={ref} className={`rough-mark rough-${kind}`} viewBox={kind === "circle" ? "0 0 204 84" : "0 0 204 36"} aria-hidden="true" />;
}
