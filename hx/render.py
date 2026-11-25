"""Render the film (or a slice) to H.264 and mux the original recording.

    python -m hx.render --out output/haoxiang-mv.mp4 --audio [--lyrics LRC|placeholder] [--draft]
                        [--t0 S --t1 S] [--workers N] [--debug]

Chunked multiprocess (the encoder settings, chunk planning and container checks are
mv.encode's): each worker pipes raw RGBA frames into its own ffmpeg, the chunks are joined with
a stream copy, and `--audio` muxes the recording named in the timeline (or a path given after
the flag) as AAC 320k from audio time 0, padded or cut to the picture. No frame touches the disk
as an image. Final 1920x1080 30 fps; --draft 960x540 15 fps (the picture is always drawn at
1920x1080 by hx.chalk and resized: the paper's tooth is made of device pixels).
"""
from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from mv.encode import FFMPEG, check_container, encoder_args, plan_chunks

from . import lyrics
from .frame import FPS

ROOT = Path(__file__).resolve().parent.parent


def _chunk(job: dict) -> dict:
    if job["lyrics"]:
        os.environ[lyrics.ENV] = job["lyrics"]
    from .frame import Renderer
    r = Renderer(job["scale"], job["debug"])
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba",
           "-s", f"{r.w}x{r.h}", "-r", str(job["fps"]), "-i", "-", "-an",
           *encoder_args(job["draft"], job["fps"]), job["path"]]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    n, t0 = 0, time.perf_counter()
    try:
        for f in range(job["f0"], job["f1"], job["step"]):
            proc.stdin.write(r.render_frame(f).tobytes())
            n += 1
    finally:
        proc.stdin.close()
        code = proc.wait()
    if code != 0:
        raise RuntimeError(f"ffmpeg failed on chunk {job['index']} (exit {code})")
    return {"index": job["index"], "frames": n, "seconds": time.perf_counter() - t0}


def mux(video: Path, audio: Path, out: Path, frames: int, fps: int, start: float = 0.0) -> dict:
    tmp = out.with_name(f".{out.stem}.muxing{out.suffix}")
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
                    "-ss", f"{start:.6f}", "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-af", "apad", "-t", f"{frames / fps:.6f}",
                    "-movflags", "+faststart", str(tmp)], check=True)
    try:
        info = check_container(tmp, frames, want_audio=True)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    tmp.replace(out)
    return info


def render(out: Path, t0=None, t1=None, draft=False, workers=None, audio: Path | None = None, debug=False,
           lyric_src: str | None = None) -> dict:
    from .timeline import get_timeline
    os.environ["HX_STRICT"] = "1"                      # a scene module that fails to import stops the render
    tl = get_timeline()
    step = 2 if draft else 1
    fps = FPS // step
    f0 = 0 if t0 is None else max(0, int(math.floor(t0 * FPS)))
    f1 = tl.n_frames if t1 is None else min(tl.n_frames, int(math.ceil(t1 * FPS)))
    f0 -= f0 % step
    total = len(range(f0, f1, step))
    if total <= 0:
        raise SystemExit("nothing to render")
    asked = workers or max(1, min(8, (os.cpu_count() or 4) - 2))
    ranges = plan_chunks(f0, f1, step, asked)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    work = out.parent / f".{out.stem}_chunks"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    jobs = [dict(index=i, f0=a, f1=b, step=step, fps=fps, scale=0.5 if draft else 1.0, draft=draft, debug=debug,
                 lyrics=lyric_src, path=str(work / f"chunk_{i:03d}.mp4")) for i, (a, b) in enumerate(ranges)]
    print(f"[render] {total} frames ({f0}..{f1 - 1} step {step}) in {len(jobs)} chunks, "
          f"{'draft 960x540' if draft else 'final 1920x1080'} @ {fps} fps, lyrics: "
          f"{'off' if not lyric_src else 'placeholder' if lyric_src == lyrics.PLACEHOLDER else 'from the LRC file'}",
          file=sys.stderr)
    wall = time.perf_counter()
    if len(jobs) == 1:
        results = [_chunk(jobs[0])]
    else:
        with mp.get_context("spawn").Pool(len(jobs)) as pool:
            results = pool.map(_chunk, jobs)
    frames = sum(r["frames"] for r in results)
    lst = work / "list.txt"
    lst.write_text("".join(f"file '{Path(j['path']).name}'\n" for j in jobs))
    video = work / "video.mp4"
    subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", "-movflags", "+faststart", str(video)], check=True)
    for j in jobs:
        Path(j["path"]).unlink(missing_ok=True)
    try:
        check_container(video, frames, want_audio=False)
        if audio:
            info = mux(video, audio, out, frames, fps, start=f0 / FPS)
        else:
            info = check_container(video, frames, want_audio=False)
            video.replace(out)
    except Exception as exc:
        raise RuntimeError(f"{exc}\n[render] the rendered picture is kept at {video}") from exc
    shutil.rmtree(work, ignore_errors=True)
    return {"out": str(out), "frames": frames, "container_frames": info.get("frames"), "start": info.get("start"),
            "duration": info.get("duration"), "video": info.get("video"), "audio": info.get("audio"),
            "wall_s": round(time.perf_counter() - wall, 1), "chunks": len(jobs),
            "size_mb": round(out.stat().st_size / 1e6, 2)}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--t0", type=float)
    ap.add_argument("--t1", type=float)
    ap.add_argument("--draft", action="store_true", help="960x540, 15 fps")
    ap.add_argument("--workers", type=int)
    ap.add_argument("--audio", nargs="?", const="", help="mux the recording (default: the one the timeline names)")
    ap.add_argument("--lyrics", metavar="LRC", help="burn in the lyric line from this .lrc file (or 'placeholder')")
    ap.add_argument("--debug", action="store_true")
    a = ap.parse_args(argv)
    src = None
    if a.lyrics:
        src = a.lyrics if a.lyrics == lyrics.PLACEHOLDER else str(Path(a.lyrics).resolve())
    audio = None
    if a.audio is not None:
        from .timeline import get_timeline
        audio = Path(a.audio) if a.audio else ROOT / get_timeline().audio
    print(json.dumps(render(Path(a.out), a.t0, a.t1, a.draft, a.workers, audio, a.debug, src), indent=1))


if __name__ == "__main__":
    main()
