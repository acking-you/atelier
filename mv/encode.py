"""Encoding helpers shared by the films: x264 settings, chunk planning, container checks.

Every film renders frames as raw RGBA, pipes them into ffmpeg (the static binary that ships
with `imageio-ffmpeg`, so no system ffmpeg or ffprobe is needed), joins GOP-aligned chunks with
a stream copy and checks the result before calling it done.

Final:  1920x1080, 30 fps, libx264 yuv420p crf 16 preset slow, aq-mode 3, closed GOP 60, bt709.
Draft:  960x540, 15 fps, preset veryfast, crf 23.
"""
from __future__ import annotations

import math
import subprocess
from pathlib import Path

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
MAX_DEFAULT_WORKERS = 8          # each final worker also runs an x264 slow encoder (about 0.6 to 0.9 GB)


def encoder_args(draft: bool, fps: int) -> list[str]:
    color = ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv"]
    # full-range RGB -> limited-range bt709 YUV; setparams tags the frames, which is what ends up in the VUI
    vf = ["-vf", "scale=in_range=full:out_range=tv:out_color_matrix=bt709:flags=accurate_rnd+full_chroma_int,"
                 "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv"]
    if draft:
        return vf + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "23",
                     "-g", str(fps * 2), "-x264-params", "open-gop=0"] + color
    return vf + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "slow", "-crf", "16",
                 "-x264-params", "aq-mode=3:keyint=60:min-keyint=60:scenecut=0:open-gop=0",
                 "-bf", "2"] + color


def probe(path: Path) -> dict:
    """Stream facts read back from the container via ffmpeg -i (no ffprobe in the wheel)."""
    out = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path), "-map", "0", "-c", "copy", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    info = {"raw": out}
    for line in out.splitlines():
        s = line.strip()
        if s.startswith("Duration:"):
            info["duration"] = s.split(",")[0].split()[1]
            info["start"] = float(s.split("start:")[1].split(",")[0])
        if s.startswith("Stream #0") and ", start " in s:        # a per-stream start offset
            info["stream_start"] = max(info.get("stream_start", 0.0), float(s.split(", start ")[1].split()[0]))
        if "Video:" in s and "video" not in info:
            info["video"] = s.split("Video:")[1].strip()
        if "Audio:" in s and "audio" not in info:
            info["audio"] = s.split("Audio:")[1].strip()
        if s.startswith("frame="):
            info["frames"] = int(s.split("frame=")[1].split()[0])
    return info


def count_frames(path: Path) -> int | None:
    """Video frames in a container (packets of the first video stream)."""
    out = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path), "-map", "0:v:0", "-c", "copy", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    n = None
    for line in out.splitlines():
        if line.strip().startswith("frame="):
            n = int(line.split("frame=")[1].split()[0])
    return n


def check_container(path: Path, frames: int, want_audio: bool) -> dict:
    """Probe a finished file and raise unless it holds exactly `frames` video frames, starts at
    zero and (if asked) carries audio."""
    info = probe(path)
    got = count_frames(path)
    info["frames"] = got
    start = max(abs(info.get("start") or 0.0), abs(info.get("stream_start") or 0.0))
    if start > 1e-6:
        raise RuntimeError(f"{path}: container / stream start is {start} s, expected 0")
    if got != frames:
        raise RuntimeError(f"{path}: container has {got} video frames, expected {frames}")
    if want_audio and "audio" not in info:
        raise RuntimeError(f"{path}: no audio stream in the container")
    return info



def plan_chunks(f0: int, f1: int, step: int, workers: int) -> list[tuple[int, int]]:
    """Frame ranges [a, b) on GOP boundaries (so that the concat is a clean stream copy), as
    many as `workers` allows: the GOPs are dealt out evenly."""
    gop = 60                                                   # source frames per GOP (60 final, 30 x step 2 draft)
    total = f1 - f0
    gops = max(1, math.ceil(total / gop))
    n = max(1, min(workers, gops))
    out, a = [], f0
    for i in range(n):
        size = (gops // n + (1 if i < gops % n else 0)) * gop
        b = min(f1, a + size)
        if a < b:
            out.append((a, b))
        a = b
    return out
