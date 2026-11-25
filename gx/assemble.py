"""Cut the generated clips to the recording's clock, add title and lyric line, mux the song.

    python -m gx.assemble --out output/haoxiang-anime.mp4 [--lyrics LRC|placeholder] [--draft]

Every shot of gx.plan fills its slot exactly: clip frame k is shown as output frame f0 + k (the
24 fps clips are played at 30 fps, so nothing is dropped or doubled). A clip that runs out holds
its last frame; a shot whose clip is missing falls back to its staged still with a slow push-in.
Fades, dissolves, the two silences, a gentle pulse of exposure on the kicks in the loud sections
and one soft flash where the cloud breaks are done here. The lyric line and the title are the
ones of hx (read from the LRC and the materials at render time; nothing is typed here). The
recording is muxed untouched (AAC 320k) from audio time 0.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import skia

from hx import credits, lyrics
from hx.render import mux
from hx.timeline import get_timeline, smoothstep
from mv.engine import palette, prims
from mv.encode import FFMPEG, check_container

from . import plan

GX = Path(__file__).resolve().parent
ROOT = GX.parent
FPS = 30
FADE_COL = {"black": (8, 9, 14), "fog": (198, 204, 214), "paper": (236, 222, 196)}
LOUD = {"chorus", "bridge", "outro"}
FLASH = "S42"                                   # the shot that opens on the band's slam at 201.25 s


class Reader:
    """Frames of one shot at the output size, in order; holds the last one when the clip ends."""

    def __init__(self, shot: plan.Shot, w: int, h: int):
        self.shot, self.w, self.h = shot, w, h
        self.last = None
        self.proc = None
        self.k = 0
        clip = GX / "shots" / f"{shot.id}.mp4"
        still = GX / "frames" / f"{shot.id}.jpg"
        vf = f"scale={w}:{h}:flags=lanczos,unsharp=5:5:0.35:5:5:0.0"
        if shot.frame and clip.exists():
            self.proc = subprocess.Popen([FFMPEG, "-hide_banner", "-loglevel", "error", "-i", str(clip), "-map", "0:v:0",
                                          "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE,
                                         stderr=subprocess.DEVNULL)
        elif shot.frame and still.exists():
            from PIL import Image
            self.still = np.asarray(Image.open(still).convert("RGB").resize((int(w * 1.12), int(h * 1.12))))
        else:
            self.still = None
        self.n_total = int(round(shot.dur * FPS))

    def next(self) -> np.ndarray:
        if self.proc is not None:
            raw = self.proc.stdout.read(self.w * self.h * 3)
            if len(raw) == self.w * self.h * 3:
                self.last = np.frombuffer(raw, dtype=np.uint8).reshape(self.h, self.w, 3)
            if self.last is None:
                self.last = np.zeros((self.h, self.w, 3), np.uint8)
        elif getattr(self, "still", None) is not None:              # slow push-in on the staged frame
            u = min(1.0, self.k / max(1, self.n_total))
            s = 1.12 - 0.10 * u
            cw, ch = int(self.w * 1.12 / s), int(self.h * 1.12 / s)
            x0, y0 = (self.still.shape[1] - cw) // 2, (self.still.shape[0] - ch) // 2
            from PIL import Image
            self.last = np.asarray(Image.fromarray(self.still[y0:y0 + ch, x0:x0 + cw]).resize((self.w, self.h)))
        else:
            self.last = np.full((self.h, self.w, 3), FADE_COL["black"], np.uint8)
        self.k += 1
        return self.last

    def close(self) -> None:
        if self.proc is not None:
            self.proc.stdout.close()
            self.proc.kill()
            self.proc.wait()


def _mix(a: np.ndarray, b, w: float) -> np.ndarray:
    if w <= 0.0:
        return a
    b = np.asarray(b, dtype=np.float32)
    return (a.astype(np.float32) * (1.0 - w) + b * w + 0.5).astype(np.uint8)


class Title:
    """Title and credits over the opening shot (read from the materials)."""

    def __init__(self, scale: float):
        self.scale = scale
        roles = credits.roles()[:2]
        self.title = prims.text_image(credits.title(), prims.SERIF_CJK, 76 * scale, palette.PAPER, tracking=0.34, weight=600)
        line = "    ".join([credits.artist()] + [f"{r} {n}" for r, n in roles])
        self.sub = prims.text_image(line, prims.SERIF_CJK, 28 * scale, palette.PAPER, tracking=0.20)

    def draw(self, frame: np.ndarray, t: float) -> np.ndarray:
        a = smoothstep(2.4, 4.0, t) * (1.0 - smoothstep(9.3, 10.8, t))
        if a <= 0.0:
            return frame
        arr = np.dstack([frame, np.full(frame.shape[:2], 255, np.uint8)])
        c = skia.Surface(arr).getCanvas()
        h, w = frame.shape[:2]
        for img, y, al in ((self.title, 0.40, 1.0), (self.sub, 0.40 + 0.085, 0.85)):
            x = (w - img.width()) / 2
            yy = h * y - img.height() / 2 + 6 * self.scale * (1 - smoothstep(2.4, 4.4, t))
            sh = skia.Paint(Color=skia.ColorSetARGB(int(150 * a), 6, 8, 14),
                            MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 14 * self.scale))
            c.drawRect(skia.Rect.MakeXYWH(x - 30, yy - 6, img.width() + 60, img.height() + 12), sh)
            c.drawImage(img, x, yy, prims.LINEAR, skia.Paint(Alphaf=a * al))
        return arr[..., :3]


def assemble(out: Path, lyric_src: str | None, draft: bool) -> dict:
    tl = get_timeline()
    w, h = (960, 540) if draft else (1920, 1080)
    scale = w / 1920
    if lyric_src:
        os.environ[lyrics.ENV] = lyric_src
    n_frames = tl.n_frames
    out.parent.mkdir(parents=True, exist_ok=True)
    video = out.with_name(f".{out.stem}.video.mp4")
    enc = subprocess.Popen([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            "-preset", "veryfast" if draft else "medium", "-crf", "24" if draft else "17",
                            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                            "-movflags", "+faststart", str(video)], stdin=subprocess.PIPE)
    title = Title(scale)
    shots = plan.SHOTS
    bounds = [int(round(s.t0 * FPS)) for s in shots] + [n_frames]
    cur = prev = None
    idx = -1
    missing = [s.id for s in shots if s.frame and not (GX / "shots" / f"{s.id}.mp4").exists()]
    for n in range(n_frames):
        t = (n + 0.5) / FPS
        while idx + 1 < len(shots) and n >= bounds[idx + 1]:
            idx += 1
            if prev is not None:
                prev.close()
            prev, cur = cur, Reader(shots[idx], w, h)
        s = shots[idx]
        f = cur.next()
        ts = t - s.t0
        if s.dissolve > 0.0 and prev is not None and ts < s.dissolve:
            f = _mix(prev.next(), f, smoothstep(0.0, s.dissolve, ts))
        if s.fade_in > 0.0 and ts < s.fade_in:
            f = _mix(f, FADE_COL["black"], 1.0 - smoothstep(0.0, s.fade_in, ts))
        if s.fade_out > 0.0 and t > s.t1 - s.fade_out:
            f = _mix(f, FADE_COL[s.fade_to], smoothstep(s.t1 - s.fade_out, s.t1, t))
        sec = tl.section_at(t)
        gain = 1.0
        if sec.kind in LOUD:                                   # the picture breathes with the kick, barely
            gain += 0.045 * tl.curve("kick", t)
        if s.id == FLASH and ts < 0.85:                        # the cloud breaks: one soft swell of light
            f = _mix(f, (255, 250, 238), 0.55 * (1.0 - smoothstep(0.0, 0.85, ts)) ** 2)
        if gain != 1.0:
            f = np.clip(f.astype(np.float32) * gain, 0, 255).astype(np.uint8)
        if t < 11.0:
            f = title.draw(np.ascontiguousarray(f), t)
        if lyric_src:
            rgba = np.dstack([f, np.full((h, w), 255, np.uint8)])
            f = lyrics.overlay(rgba, tl, t, scale)[..., :3]
        enc.stdin.write(np.ascontiguousarray(f).tobytes())
        if n % 900 == 0:
            print(f"[assemble] {n}/{n_frames}", file=sys.stderr)
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("encoder failed")
    check_container(video, n_frames, want_audio=False)
    info = mux(video, ROOT / tl.audio, out, n_frames, FPS)
    video.unlink(missing_ok=True)
    return {"out": str(out), "frames": n_frames, "duration": info.get("duration"), "video": info.get("video"),
            "audio": info.get("audio"), "size_mb": round(out.stat().st_size / 1e6, 1), "missing_clips": missing}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lyrics", metavar="LRC")
    ap.add_argument("--draft", action="store_true")
    a = ap.parse_args(argv)
    src = None
    if a.lyrics:
        src = a.lyrics if a.lyrics == lyrics.PLACEHOLDER else str(Path(a.lyrics).resolve())
    print(json.dumps(assemble(Path(a.out), src, a.draft), indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
