#!/usr/bin/env python3
# Copyright (c) 2026 Achyuth Jayadevan <achyuth@jayadevan.in>
# SPDX-License-Identifier: MIT
# Licensed under the MIT License. See LICENSE in the repository root.

"""Generate and sample-lock a MimikaStudio voice track for the Manim film."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def request_json(url: str, payload: dict | None = None, timeout: int = 240) -> dict:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"MimikaStudio returned HTTP {exc.code}: {detail}") from exc


def run(*args: str, capture: bool = False) -> str:
    result = subprocess.run(
        args,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    return result.stdout if capture else ""


def probe(path: Path) -> dict:
    output = run(
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a:0",
        "-show_entries",
        "stream=sample_rate,channels,duration_ts,time_base:format=duration",
        "-of",
        "json",
        str(path),
        capture=True,
    )
    return json.loads(output)


def duration_seconds(path: Path) -> float:
    return float(probe(path)["format"]["duration"])


def measure_loudnorm(path: Path) -> dict:
    result = subprocess.run(
        (
            "ffmpeg",
            "-hide_banner",
            "-nostats",
            "-i",
            str(path),
            "-af",
            "loudnorm=I=-16:LRA=7:TP=-1.5:print_format=json",
            "-f",
            "null",
            "-",
        ),
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    matches = re.findall(r"\{\s*\"input_i\".*?\}", result.stderr, flags=re.DOTALL)
    if not matches:
        raise RuntimeError("ffmpeg loudnorm analysis did not return JSON")
    return json.loads(matches[-1])


def frame_timestamp(frame: int, fps: int) -> str:
    total_ms = round(frame * 1000 / fps)
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, milliseconds = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def validate_timeline(timeline: dict, video: Path) -> tuple[int, int, int]:
    fps = int(timeline["fps"])
    sample_rate = int(timeline["sample_rate"])
    if sample_rate % fps:
        raise ValueError("sample_rate must be exactly divisible by fps")
    samples_per_frame = sample_rate // fps

    cues = timeline["cues"]
    if not cues or int(cues[0]["start_frame"]) != 0:
        raise ValueError("timeline must begin at frame zero")
    for previous, current in zip(cues, cues[1:]):
        if int(previous["end_frame"]) != int(current["start_frame"]):
            raise ValueError(f"gap or overlap between cues {previous['id']} and {current['id']}")
    for cue in cues:
        if int(cue["end_frame"]) <= int(cue["start_frame"]):
            raise ValueError(f"cue {cue['id']} has a non-positive duration")

    video_probe = json.loads(
        run(
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-count_frames",
            "-show_entries",
            "stream=nb_read_frames,r_frame_rate",
            "-of",
            "json",
            str(video),
            capture=True,
        )
    )
    stream = video_probe["streams"][0]
    numerator, denominator = (int(part) for part in stream["r_frame_rate"].split("/"))
    actual_fps = numerator / denominator
    if not math.isclose(actual_fps, fps, rel_tol=0, abs_tol=1e-9):
        raise ValueError(f"video is {actual_fps} fps; timeline requires {fps} fps")
    video_frames = int(stream["nb_read_frames"])
    final_frame = int(cues[-1]["end_frame"])
    if video_frames != final_frame:
        raise ValueError(f"video has {video_frames} frames; timeline ends at {final_frame}")
    return fps, sample_rate, samples_per_frame


def generation_payload(cue: dict, timeline: dict) -> dict:
    return {
        "text": cue["text"],
        "mode": "clone",
        "voice_name": timeline["voice"],
        "language": "English",
        "speed": 1.0,
        "model_size": timeline["model_size"],
        "model_quantization": timeline["model_quantization"],
        "temperature": 0.75,
        "top_p": 0.9,
        "top_k": 40,
        "repetition_penalty": 1.05,
        "seed": 2100 + int(cue["id"]),
        "unload_after": False,
    }


def generation_fingerprint(cue: dict, timeline: dict) -> str:
    encoded = json.dumps(
        generation_payload(cue, timeline),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def generate_raw(
    base_url: str,
    cue: dict,
    timeline: dict,
    destination: Path,
) -> dict:
    payload = generation_payload(cue, timeline)
    result = request_json(f"{base_url}/api/qwen3/generate", payload)
    audio_url = result["audio_url"]
    with urllib.request.urlopen(f"{base_url}{audio_url}", timeout=60) as response:
        destination.write_bytes(response.read())
    return {"mimika_filename": result["filename"], "mimika_audio_url": audio_url}


def fit_slot(
    raw: Path,
    slot: Path,
    slot_samples: int,
    sample_rate: int,
    min_occupancy: float,
    max_tempo: float,
) -> tuple[float, float]:
    raw_seconds = duration_seconds(raw)
    slot_seconds = slot_samples / sample_rate
    available_seconds = max(0.25, slot_seconds - 0.22)
    occupancy = raw_seconds / slot_seconds
    if occupancy < min_occupancy:
        raise RuntimeError(
            f"{raw.name} occupies only {occupancy:.1%} of its {slot_seconds:.3f}s panel; expand its narration"
        )
    tempo = max(1.0, raw_seconds / available_seconds)
    if tempo > max_tempo:
        raise RuntimeError(
            f"{raw.name} needs {tempo:.3f}x compression to fit {slot_seconds:.3f}s; shorten its narration"
        )

    run(
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(raw),
        "-af",
        (
            f"aresample={sample_rate},atempo={tempo:.9f},"
            f"apad=whole_len={slot_samples},atrim=end_sample={slot_samples},asetpts=N/SR/TB"
        ),
        "-ar",
        str(sample_rate),
        "-ac",
        "1",
        "-c:a",
        "pcm_s24le",
        str(slot),
    )
    slot_probe = probe(slot)["streams"][0]
    actual_samples = int(slot_probe["duration_ts"])
    if actual_samples != slot_samples:
        raise RuntimeError(f"{slot.name}: expected {slot_samples} samples, got {actual_samples}")
    return raw_seconds, tempo


def write_srt(timeline: dict, output: Path) -> None:
    fps = int(timeline["fps"])
    blocks = []
    for cue in timeline["cues"]:
        blocks.append(
            "\n".join(
                [
                    str(cue["id"]),
                    f"{frame_timestamp(cue['start_frame'], fps)} --> {frame_timestamp(cue['end_frame'], fps)}",
                    cue["text"],
                ]
            )
        )
    output.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:7693")
    parser.add_argument("--timeline", type=Path, required=True)
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--min-occupancy", type=float, default=0.90)
    parser.add_argument("--max-tempo", type=float, default=1.08)
    args = parser.parse_args()

    for executable in ("ffmpeg", "ffprobe"):
        if shutil.which(executable) is None:
            raise RuntimeError(f"required executable not found: {executable}")

    timeline = json.loads(args.timeline.read_text(encoding="utf-8"))
    fps, sample_rate, samples_per_frame = validate_timeline(timeline, args.video)
    health = request_json(f"{args.base_url}/api/health")
    if health.get("status") != "ok":
        raise RuntimeError(f"MimikaStudio health check failed: {health}")
    voices = request_json(f"{args.base_url}/api/voice-prompts").get("voices", [])
    voice = next((item for item in voices if item.get("name") == timeline["voice"]), None)
    if voice is None:
        raise RuntimeError(f"MimikaStudio voice not found: {timeline['voice']}")

    raw_dir = args.output_dir / "raw"
    slot_dir = args.output_dir / "slots"
    raw_dir.mkdir(parents=True, exist_ok=True)
    slot_dir.mkdir(parents=True, exist_ok=True)
    state_path = args.output_dir / "generation_state.json"
    state = {"cues": []}
    if args.resume and state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    state_by_id = {int(item["id"]): item for item in state.get("cues", [])}

    records = []
    for cue in timeline["cues"]:
        cue_id = int(cue["id"])
        raw = raw_dir / f"{cue_id:03d}.wav"
        slot = slot_dir / f"{cue_id:03d}.wav"
        api_record = state_by_id.get(cue_id, {})
        fingerprint = generation_fingerprint(cue, timeline)
        cache_matches = api_record.get("generation_fingerprint") == fingerprint
        if not (args.resume and raw.exists() and cache_matches):
            started = time.monotonic()
            api_record = generate_raw(args.base_url, cue, timeline, raw)
            api_record["generation_seconds"] = round(time.monotonic() - started, 3)
        slot_samples = (int(cue["end_frame"]) - int(cue["start_frame"])) * samples_per_frame
        raw_seconds, tempo = fit_slot(
            raw,
            slot,
            slot_samples,
            sample_rate,
            args.min_occupancy,
            args.max_tempo,
        )
        record = {
            "id": cue_id,
            "start_frame": int(cue["start_frame"]),
            "end_frame": int(cue["end_frame"]),
            "start_sample": int(cue["start_frame"]) * samples_per_frame,
            "end_sample": int(cue["end_frame"]) * samples_per_frame,
            "slot_samples": slot_samples,
            "slot_seconds": round(slot_samples / sample_rate, 6),
            "raw_seconds": round(raw_seconds, 6),
            "occupancy": round(raw_seconds / (slot_samples / sample_rate), 9),
            "tempo": round(tempo, 9),
            "generation_fingerprint": fingerprint,
            **api_record,
        }
        records.append(record)
        state_path.write_text(
            json.dumps(
                {
                    "voice": timeline["voice"],
                    "fps": fps,
                    "sample_rate": sample_rate,
                    "cues": records,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(
            f"[{cue_id:02d}/{len(timeline['cues'])}] "
            f"raw={raw_seconds:.3f}s slot={slot_samples / sample_rate:.3f}s tempo={tempo:.4f}"
        )
        sys.stdout.flush()

    concat_path = args.output_dir / "slots.ffconcat"
    concat_path.write_text(
        "ffconcat version 1.0\n"
        + "".join(f"file '{slot.resolve().as_posix()}'\n" for slot in sorted(slot_dir.glob("*.wav"))),
        encoding="utf-8",
    )
    raw_master = args.output_dir / "RazorProof_Manipal_TTS_48k_PCM_raw.wav"
    run(
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_path),
        "-c:a",
        "pcm_s24le",
        str(raw_master),
    )
    total_samples = int(timeline["cues"][-1]["end_frame"]) * samples_per_frame
    raw_master_stream = probe(raw_master)["streams"][0]
    if int(raw_master_stream["duration_ts"]) != total_samples:
        raise RuntimeError(
            f"raw master has {raw_master_stream['duration_ts']} samples; expected {total_samples}"
        )

    loudness_input = measure_loudnorm(raw_master)
    loudness_filter = (
        "loudnorm=I=-16:LRA=7:TP=-1.5:"
        f"measured_I={loudness_input['input_i']}:"
        f"measured_LRA={loudness_input['input_lra']}:"
        f"measured_TP={loudness_input['input_tp']}:"
        f"measured_thresh={loudness_input['input_thresh']}:"
        f"offset={loudness_input['target_offset']}:linear=false,"
        f"aresample={sample_rate},apad=whole_len={total_samples},"
        f"atrim=end_sample={total_samples},asetpts=N/SR/TB"
    )
    master = args.output_dir / "RazorProof_Manipal_TTS_48k_PCM.wav"
    run(
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(raw_master),
        "-af",
        loudness_filter,
        "-ar",
        str(sample_rate),
        "-ac",
        "1",
        "-c:a",
        "pcm_s24le",
        str(master),
    )
    master_stream = probe(master)["streams"][0]
    if int(master_stream["duration_ts"]) != total_samples:
        raise RuntimeError(
            f"master has {master_stream['duration_ts']} samples; expected {total_samples}"
        )

    loudness_output = measure_loudnorm(master)
    srt = args.output_dir / "RazorProof_Manipal_TTS_frame_locked.srt"
    write_srt(timeline, srt)
    lossless = args.output_dir / "RazorProof_Pitch_Manipal_TTS_1080p60.mov"
    delivery = args.output_dir / "RazorProof_Pitch_Manipal_TTS_1080p60.mp4"
    run(
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(args.video),
        "-i",
        str(master),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "pcm_s24le",
        "-ar",
        str(sample_rate),
        "-movflags",
        "+faststart",
        str(lossless),
    )
    run(
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(args.video),
        "-i",
        str(master),
        "-i",
        str(srt),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-map",
        "2:s:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        str(sample_rate),
        "-c:s",
        "mov_text",
        "-disposition:s:0",
        "0",
        "-movflags",
        "+faststart",
        str(delivery),
    )

    report = {
        "voice": voice,
        "engine": timeline["engine"],
        "model_size": timeline["model_size"],
        "model_quantization": timeline["model_quantization"],
        "fps": fps,
        "sample_rate": sample_rate,
        "samples_per_frame": samples_per_frame,
        "video_frames": int(timeline["cues"][-1]["end_frame"]),
        "audio_samples": total_samples,
        "boundary_drift_samples": 0,
        "boundary_drift_ms": 0.0,
        "min_occupancy": min(record["occupancy"] for record in records),
        "max_tempo": max(record["tempo"] for record in records),
        "loudness": {
            "target_i_lufs": -16.0,
            "target_true_peak_dbfs": -1.5,
            "input": loudness_input,
            "output": loudness_output,
        },
        "lossless_master": str(lossless.resolve()),
        "delivery_mp4": str(delivery.resolve()),
        "subtitle_track": str(srt.resolve()),
        "cues": records,
    }
    (args.output_dir / "SYNC_QA.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: report[key] for key in (
        "voice", "fps", "sample_rate", "video_frames", "audio_samples",
        "boundary_drift_ms", "max_tempo", "lossless_master", "delivery_mp4"
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
