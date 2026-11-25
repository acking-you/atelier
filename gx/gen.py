"""Generate the film's references, staged first frames and video clips through the local grok CLI.

    python -m gx.gen refs   [--only a,b] [--jobs 4] [--force]
    python -m gx.gen frames [--only S03,S04] [--jobs 4] [--force]
    python -m gx.gen videos [--only ...] [--jobs 3] [--force]
    python -m gx.gen sheet frames|refs|videos            # contact sheet into gx/logs/

Every item is one headless grok call that makes exactly one Imagine tool call; the result is
copied to gx/refs, gx/frames or gx/shots and the call's JSON is kept in gx/logs. Existing files
are skipped, so the run is resumable. Prompts describe pictures in our own words: no lyric text
is ever sent.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import plan

GX = Path(__file__).resolve().parent
REFS, FRAMES, SHOTS, LOGS = GX / "refs", GX / "frames", GX / "shots", GX / "logs"
PATH_RE = re.compile(r"(/Users/[^\s\"'`]+?\.(?:jpe?g|png|mp4|webp))", re.I)


def grok(tool: str, args: dict, dest: Path, tag: str, timeout: int = 900) -> str | None:
    """One tool call. Returns None on success, else the error text."""
    prompt = (f"Call the {tool} tool exactly once with exactly these arguments (JSON): {json.dumps(args, ensure_ascii=False)}\n"
              "Do not call any other tool and do not change the prompt. Then reply with only the absolute path of the "
              "generated file, or, if the tool fails or is refused, the exact error text prefixed with ERROR:")
    cmd = ["grok", "-p", prompt, "--tools", tool, "--always-approve", "--output-format", "json", "--cwd", str(GX)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout
    except subprocess.TimeoutExpired:
        return "timeout"
    (LOGS / f"{tag}.json").write_text(out)
    try:
        text = json.loads(out[out.index("{"):]).get("text", "")
    except Exception:
        text = out
    m = [p for p in PATH_RE.findall(text) if Path(p).exists() and ".grok/sessions" in p]
    if not m:
        return (text or "no output").strip()[-400:]
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(m[-1], dest)
    return None


def _ref_paths(names) -> list[str]:
    return [str(FRAMES / f"{n[1:]}.jpg") if n.startswith("@") else str(REFS / f"{n}.jpg") for n in names]


def job_ref(name: str):
    spec = plan.REFS[name]
    dest = REFS / f"{name}.jpg"
    if spec.get("from"):
        return grok("image_edit", {"prompt": spec["prompt"], "image": _ref_paths(spec["from"]), "aspect_ratio": "16:9"},
                    dest, f"ref_{name}")
    return grok("image_gen", {"prompt": spec["prompt"], "aspect_ratio": "16:9"}, dest, f"ref_{name}")


def job_frame(shot: plan.Shot):
    dest = FRAMES / f"{shot.id}.jpg"
    prompt = f"{shot.frame} {plan.look(shot)}"
    if shot.refs:
        return grok("image_edit", {"prompt": prompt, "image": _ref_paths(shot.refs), "aspect_ratio": "16:9"},
                    dest, f"frame_{shot.id}")
    return grok("image_gen", {"prompt": prompt, "aspect_ratio": "16:9"}, dest, f"frame_{shot.id}")


def job_video(shot: plan.Shot):
    dest = SHOTS / f"{shot.id}.mp4"
    people = [r for r in shot.refs if r in ("boy", "girl")]
    args = {"prompt": f"{shot.motion} {plan.look(shot)}", "first_frame": str(FRAMES / f"{shot.id}.jpg"),
            "aspect_ratio": "16:9", "duration": shot.gen_seconds, "resolution_name": "720p"}
    if people:
        args["images"] = _ref_paths(people)
    return grok("reference_to_video", args, dest, f"video_{shot.id}", timeout=1500)


def run(kind: str, only, jobs: int, force: bool) -> None:
    if kind == "refs":
        items = [(n, REFS / f"{n}.jpg", job_ref, n) for n in plan.REFS]
    elif kind == "frames":
        items = [(s.id, FRAMES / f"{s.id}.jpg", job_frame, s) for s in plan.SHOTS if s.frame]
    else:
        items = [(s.id, SHOTS / f"{s.id}.mp4", job_video, s) for s in plan.SHOTS if s.frame]
    if only:
        items = [it for it in items if it[0] in only]
    todo = [it for it in items if force or not it[1].exists()]
    print(f"[{kind}] {len(items) - len(todo)} done, {len(todo)} to make, {jobs} at a time", file=sys.stderr)
    LOGS.mkdir(exist_ok=True)

    def one(it):
        t0 = time.time()
        err = it[2](it[3])
        if err:                                   # one retry for transient failures, never for refusals
            if not re.search(r"moderat|safety|policy|refus|upgrade|limit|quota", err, re.I):
                err = it[2](it[3])
        print(f"  {it[0]:10s} {'ok' if not err else 'FAILED: ' + err[:160]}  ({time.time() - t0:.0f} s)", file=sys.stderr)
        return it[0], err

    if kind == "refs":                            # references that derive from others must wait for them
        first = [it for it in todo if not plan.REFS[it[0]].get("from")]
        later = [it for it in todo if plan.REFS[it[0]].get("from")]
        batches = [first, later]
    else:
        batches = [todo]
    failed = []
    for batch in batches:
        with ThreadPoolExecutor(jobs) as ex:
            failed += [r for r in ex.map(one, batch) if r[1]]
    print(f"[{kind}] finished; {len(failed)} failed: {[f[0] for f in failed]}", file=sys.stderr)


def sheet(kind: str, cols: int = 6) -> None:
    from PIL import Image, ImageDraw
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    tw, th = 480, 270
    tiles = []
    if kind == "refs":
        tiles = [(n, Image.open(REFS / f"{n}.jpg")) for n in plan.REFS if (REFS / f"{n}.jpg").exists()]
    elif kind == "frames":
        tiles = [(s.id, Image.open(FRAMES / f"{s.id}.jpg")) for s in plan.SHOTS if (FRAMES / f"{s.id}.jpg").exists()]
    else:                                         # the middle and the last frame of every clip
        import numpy as np
        for s in plan.SHOTS:
            p = SHOTS / f"{s.id}.mp4"
            if not p.exists():
                continue
            for lab, ss in (("m", s.gen_seconds * 0.5), ("e", max(0.0, s.use_seconds - 0.2))):
                raw = subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-ss", f"{ss:.2f}", "-i", str(p),
                                      "-frames:v", "1", "-vf", f"scale={tw}:{th}", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                      "-"], capture_output=True).stdout
                if len(raw) == tw * th * 3:
                    tiles.append((f"{s.id}{lab}", Image.frombuffer("RGB", (tw, th), raw)))
    rows = math.ceil(len(tiles) / cols)
    out = Image.new("RGB", (cols * tw, rows * th))
    for i, (name, im) in enumerate(tiles):
        im = im.convert("RGB").resize((tw, th))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 8 + 7 * len(name), 14), fill=(0, 0, 0))
        d.text((3, 2), name, fill=(255, 255, 255))
        out.paste(im, ((i % cols) * tw, (i // cols) * th))
    dest = LOGS / f"sheet_{kind}.jpg"
    out.save(dest, quality=85)
    print(dest, len(tiles), "tiles")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=["refs", "frames", "videos", "sheet"])
    ap.add_argument("what", nargs="?")
    ap.add_argument("--only")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--cols", type=int, default=6)
    a = ap.parse_args(argv)
    if a.kind == "sheet":
        sheet(a.what or "frames", a.cols)
    else:
        run(a.kind, set(a.only.split(",")) if a.only else None, a.jobs, a.force)


if __name__ == "__main__":
    main()
