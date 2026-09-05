#!/bin/sh
# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"

MANIM="$SCRIPT_DIR/.venv/bin/manim"
SCENES="OpeningProof LostCoordinate InvariantScanner BoundaryFailures FailureChains SemanticFirewall ProviderEvidence FinalProof"

mkdir -p renders

"$MANIM" -qh master_video_3b1b.py $SCENES

ffmpeg -hide_banner -loglevel warning -y \
  -f concat -safe 0 -i concat.txt \
  -c copy -movflags +faststart \
  renders/RazorProof_Pitch_Silent_1080p60.mp4

ffprobe -v error \
  -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate \
  -of default=noprint_wrappers=1 \
  renders/RazorProof_Pitch_Silent_1080p60.mp4
