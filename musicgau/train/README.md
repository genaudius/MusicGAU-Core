# Training MusicGAU (AudioCraft MusicGen + LoRA)

## Dataset format
This repo produces AudioCraft-friendly manifests:
- `.../manifests/train.jsonl(.gz)`
- `.../manifests/valid.jsonl(.gz)`
- `.../manifests/test.jsonl(.gz)`

Each row contains at minimum:
- `path`: path to WAV clip
- `text`: conditioning prompt (we also keep `description`)

## Typical flow
1) Prepare clips + manifests (stereo, 32kHz):

```bash
python -m musicgau.pipeline.prepare_dataset run --input-dir "PATH_TO_MASTERS" --output-dir datasets/musicgau_clips
```

2) (Optional) Enrich manifests with Spotify/Last.fm, producing stronger `text` prompts:

```bash
python -m musicgau.integrations.enrich_manifest run \
  --manifest-in datasets/musicgau_clips/manifests/train.jsonl.gz \
  --manifest-out datasets/musicgau_clips/manifests/train.enriched.jsonl.gz \
  --local-meta-json data/local_track_meta.json
```

3) Train with AudioCraft:
- `python -m musicgau.train.run_audiocraft train --dry-run true`

