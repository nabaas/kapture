# Videos

Standalone project. Builds short videos (slide-based talking-head style) from
a markdown script.

The pipeline is split into three independent stages so you can run any one
of them without the others:

1. **`script.py`** — turn a markdown brief into a clean script with
   per-slide segments.
2. **`tts.py`** — render each segment to an audio file. By default this
   uses a stub that writes silent WAVs so the pipeline runs end-to-end
   without a TTS provider; plug in your own provider in `synthesize()`.
3. **`compose.py`** — render a slide PNG per segment with Pillow, then
   stitch slides + audio into an `.mp4` using `ffmpeg`.

No autonomous publishing. The pipeline produces a file at
`output/<slug>.mp4`. What you do with it after that is up to you.

## Layout

```
videos/
├─ README.md
├─ requirements.txt
├─ src/
│  ├─ __init__.py
│  ├─ script.py
│  ├─ tts.py
│  ├─ compose.py
│  └─ build_video.py     # orchestrates 1→2→3
├─ assets/               # fonts, intro/outro stills (optional)
└─ output/
```

## Usage

```bash
cd videos
pip install -r requirements.txt
# ffmpeg must be on your PATH for compose.py to produce mp4

# End-to-end from a markdown brief
python -m src.build_video \
    --input ../claude_research_stack/reports/2026-05-08T1300.md \
    --slug today

# Stages individually
python -m src.script   --input ... --output output/today.script.json
python -m src.tts      --script output/today.script.json --output output/today.audio/
python -m src.compose  --script output/today.script.json --audio-dir output/today.audio/ --output output/today.mp4
```

## Pluggable TTS

`src/tts.py::synthesize(text, out_path)` is the seam. The default
implementation writes a 1-second silent WAV so the rest of the pipeline
is exercisable. Replace it with a call to your TTS provider of choice
(ElevenLabs, OpenAI TTS, Coqui, Piper, etc.). Provider keys go in env
vars; do not commit them.
