"""Build hx/data/timeline.json from the recording and its LRC (run once; the film reads only the JSON).

    python -m hx.analyze

The recording is click-steady: 80 BPM, beat k at BEAT0 + 0.75 k for the whole file (measured
by folding the spectral flux at 0.75 s in 8 s windows: the phase holds at 0.265 +- 0.01 from
the first bar to the coda, across both silences). Bars are 4 beats; phrases start on beat
k = 16, 32, 48, 64 in the first half and on k = 122 + 16 n afterwards, so one two-beat bar sits
in the interlude (k = 120..122). No lyric text is stored: cues carry the 0-based LRC line
index, its stamp, its character count and the time the line may stay up.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference" / "haoxiangaizhegeshijie"
AUDIO = REF / "haoxiangaizhegeshijie.mp3"
LRC = REF / "haoxiangaizhegeshijie.lrc"
OUT = Path(__file__).resolve().parent / "data" / "timeline.json"

FPS = 30
BEAT0, BEAT_S = 0.265, 0.75
CURVE_HZ = 60
HEADER_LINES = 4            # LRC lines 0..3 are credits, not sung

# (id, t0, kind, hope): hope is the film's one dial from weight (0) to light (1) at the section's start
SECTIONS = [
    ("intro", 0.0, "intro", 0.00),
    ("v1a", 12.265, "verse", 0.02),
    ("v1b", 24.265, "verse", 0.03),
    ("p1a", 36.265, "pre", 0.05),
    ("p1b", 48.265, "pre", 0.05),
    ("hush1", 56.0, "silence", 0.03),
    ("c1a", 58.6, "chorus", 0.04),
    ("c1b", 70.7, "chorus", 0.10),
    ("inter", 80.5, "interlude", 0.18),
    ("v2a", 91.765, "verse", 0.20),
    ("v2b", 103.765, "verse", 0.20),
    ("p2a", 115.765, "pre", 0.24),
    ("p2b", 127.765, "pre", 0.28),
    ("c2a", 138.2, "chorus", 0.28),
    ("c2b", 150.1, "chorus", 0.36),
    ("br_a", 158.86, "bridge", 0.48),
    ("br_b", 170.765, "bridge", 0.60),
    ("br_c", 178.265, "bridge", 0.70),
    ("bd", 182.3, "breakdown", 0.70),
    ("hush2", 193.0, "silence", 0.76),
    ("c3a", 200.4, "chorus", 0.84),
    ("c3b", 213.1, "chorus", 0.92),
    ("out", 226.765, "outro", 1.00),
    ("coda", 244.5, "coda", 0.90),
]
HOPE_EXTRA = [(217.84, 0.94), (220.6, 1.0), (258.8, 0.92)]      # colour arrives with LRC line 62
MAX_HOLD = 9.0


def read_lrc():
    rows = []
    for i, raw in enumerate(LRC.read_text(encoding="utf-8").splitlines()):
        m = re.match(r"\[(\d+):(\d+(?:\.\d+)?)\](.*)", raw)
        if not m:
            continue
        groups = [len(g) for g in m.group(3).split()]          # phrase groups (character counts only)
        rows.append((i, int(m.group(1)) * 60 + float(m.group(2)), sum(groups), groups))
    return rows


def main():
    import librosa
    y, sr = librosa.load(AUDIO, sr=22050, mono=True)
    dur = len(y) / sr
    n_frames = int(np.ceil(dur * FPS - 1e-6))
    hop = 128
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    ft = np.arange(S.shape[1]) * hop / sr
    X = np.log1p(10 * S)

    def flux(lo, hi):
        m = (freqs >= lo) & (freqs < hi)
        return np.r_[0.0, np.maximum(0, np.diff(X[m], axis=1)).sum(0)]

    rms = np.sqrt((S ** 2).mean(0)) + 1e-9
    db = 20 * np.log10(rms / np.percentile(rms, 99))
    ct = np.arange(0, dur, 1.0 / CURVE_HZ)

    def smooth(v, seconds):
        k = max(1, int(seconds * sr / hop))
        w = np.hanning(k * 2 + 1)
        return np.convolve(v, w / w.sum(), "same")

    def unit(v, lo, hi):
        return np.clip((np.interp(ct, ft, v) - lo) / (hi - lo), 0, 1)

    loud = unit(smooth(db, 0.8), -24.0, 0.0)            # slow loudness, 0 = silence, 1 = full band
    fast = unit(smooth(db, 0.06), -24.0, 2.0)           # quick envelope (breath of the voice, hits)
    fl_all, fl_low = flux(30, 8000), flux(30, 160)
    hit = unit(smooth(fl_all, 0.02), np.percentile(fl_all, 50), np.percentile(fl_all, 99.7))
    kick = unit(smooth(fl_low, 0.02), np.percentile(fl_low, 60), np.percentile(fl_low, 99.7))
    cent = (freqs[:, None] * S).sum(0) / (S.sum(0) + 1e-9)
    bright = unit(smooth(cent, 0.8), 600.0, 3200.0)

    # strong onsets (for the sparse hits of the breakdown and the entries after the silences)
    env = smooth(fl_all, 0.015)
    pk = librosa.util.peak_pick(env, pre_max=12, post_max=12, pre_avg=40, post_avg=40,
                                delta=float(np.percentile(env, 92)) * 0.5, wait=20)
    top = np.percentile(env, 99.9)
    onsets = [[round(float(ft[i]), 3), round(float(min(1.0, env[i] / top)), 3)] for i in pk]

    n_beats = int((dur - BEAT0) / BEAT_S) + 1
    beats = [round(BEAT0 + BEAT_S * k, 4) for k in range(n_beats)]
    bar_k = list(range(0, 120, 4)) + list(range(122, n_beats, 4))       # one 2-beat bar: k = 120, 121
    bar_k.insert(30, 120)
    bars = [round(BEAT0 + BEAT_S * k, 4) for k in sorted(set(bar_k))]

    rows = read_lrc()
    stamps = [r[1] for r in rows]
    cues = []
    for j, (i, t, n, groups) in enumerate(rows):
        if n == 0 or i < HEADER_LINES:
            continue
        nxt = stamps[j + 1] if j + 1 < len(rows) else dur
        nxt_is_text = j + 1 < len(rows) and rows[j + 1][2] > 0
        t_end = min(nxt, t + MAX_HOLD, dur - 3.4)        # the last line leaves with the last sound (about 255.5)
        sec = [s for s in SECTIONS if s[1] <= t + 0.35][-1][0]
        cues.append({"lrc": i, "t": round(t, 3), "t_end": round(t_end, 3), "n_chars": n, "groups": groups,
                     "next_is_text": bool(nxt_is_text), "section": sec})

    sections = []
    for j, (sid, t0, kind, hope) in enumerate(SECTIONS):
        t1 = SECTIONS[j + 1][1] if j + 1 < len(SECTIONS) else n_frames / FPS
        m = (ct >= t0) & (ct < t1)
        sections.append({"id": sid, "t0": t0, "t1": round(t1, 4), "kind": kind, "hope": hope,
                         "loud": round(float(loud[m].mean()), 3),
                         "lrc": [c["lrc"] for c in cues if c["section"] == sid]})
    hope = sorted([(s[1], s[3]) for s in SECTIONS] + HOPE_EXTRA)
    data = {
        "meta": {"audio": str(AUDIO.relative_to(ROOT)), "lrc": str(LRC.relative_to(ROOT)), "duration": round(dur, 4),
                 "fps": FPS, "n_frames": n_frames, "bpm": 80.0, "beat0": BEAT0, "beat_s": BEAT_S,
                 "curve_hz": CURVE_HZ},
        "sections": sections, "cues": cues, "beats": beats, "bars": bars,
        "hope": [[t, h] for t, h in hope], "onsets": onsets,
        "curves": {k: [round(float(x), 3) for x in v]
                   for k, v in dict(loud=loud, fast=fast, hit=hit, kick=kick, bright=bright).items()},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, separators=(",", ":")))
    print(f"{OUT}: {dur:.3f} s, {n_frames} frames, {len(beats)} beats, {len(bars)} bars, {len(cues)} cues, "
          f"{len(onsets)} onsets")
    for s in sections:
        print(f"  {s['id']:6s} {s['t0']:8.3f} {s['t1']:8.3f}  {s['kind']:9s} loud {s['loud']:.2f}  hope {s['hope']:.2f}  lrc {s['lrc']}")
    bd = [o for o in onsets if 182.0 <= o[0] <= 201.5]
    print("  breakdown onsets:", bd)


if __name__ == "__main__":
    main()
