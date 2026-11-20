#!/usr/bin/env bash
# Phase 6.5 step 9 (doc §6 item 4): frames every two seconds, distinct-frame groups, local transcript.
# Usage: bash scratch/p65-s9-check.sh <video.mp4> <outDir>
set -euo pipefail
video="$1"; out="$2"
mkdir -p "$out/frames"
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height -of compact "$video" > "$out/probe.txt"
ffmpeg -v error -y -i "$video" -vf fps=1/2 "$out/frames/f%03d.png"
ffmpeg -v error -y -i "$video" -ac 1 -ar 16000 -f s16le "$out/audio.raw"
uv run --no-project --with pillow==11.0.0 --with numpy==2.1.3 python -I - "$out" <<'PY'
import glob, json, sys, numpy as np
from PIL import Image
out = sys.argv[1]
fs = sorted(glob.glob(f"{out}/frames/f*.png"))
A = [np.asarray(Image.open(f).convert("L"), dtype=np.int16) for f in fs]
groups = [[fs[0]]]
for i in range(1, len(fs)):
    if (np.abs(A[i] - A[i - 1]) > 24).sum() > 150:
        groups.append([fs[i]])
    else:
        groups[-1].append(fs[i])
json.dump(groups, open(f"{out}/frame-groups.json", "w"), indent=0)
print(len(fs), "frames,", len(groups), "distinct; read the last of each:")
print(" ".join(g[-1].rsplit("/", 1)[1] for g in groups))
PY
uv run --no-project --with faster-whisper==1.2.1 python -I - "$out" <<'PY' 2>&1 | grep -v HF_TOKEN
import json, sys, numpy as np
from faster_whisper import WhisperModel
out = sys.argv[1]
a = np.frombuffer(open(f"{out}/audio.raw", "rb").read(), dtype=np.int16).astype(np.float32) / 32768
m = WhisperModel("medium.en", device="cpu", compute_type="int8", cpu_threads=16)
segs, _ = m.transcribe(a, beam_size=5)
rows = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
json.dump(rows, open(f"{out}/transcript.json", "w"), indent=1)
open(f"{out}/transcript.txt", "w").write("\n".join(f"[{r['start']:7.2f}-{r['end']:7.2f}] {r['text']}" for r in rows) + "\n")
print("segments", len(rows))
PY
