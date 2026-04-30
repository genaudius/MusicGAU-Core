# GenAudius on RunPod 🚀

## Deployment Options

### 1. Serverless Endpoint (Recommended for SaaS)
Use this for the unified API (Generation, Stem Separation, Audio-to-MIDI).

- **Docker Image:** `your-docker-hub-user/musicgau-core:latest`
- **Environment Variables:**
    - `RUNPOD_SERVERLESS=true`
    - `SPOTIPY_CLIENT_ID=...`
    - `SPOTIPY_CLIENT_SECRET=...`
    - `LASTFM_API_KEY=...`
- **Handler:** `python -u deploy/runpod_handler.py` (Default in Dockerfile)

### 2. GPU Pod (Recommended for Batch Processing & Training)
Use this for processing massive datasets from your local drive or S3.

- **Storage:** Mount a Network Volume at `/workspace`.
- **Command:** `tail -f /dev/null` (To keep it alive) or `./scripts/runpod_train.sh`.

## API Usage (Serverless)

### Stem Separation
```json
{
    "input": {
        "task": "separate",
        "audio_url": "https://api.genaudius.studio/inputs/song.mp3"
    }
}
```

### Audio-to-MIDI
```json
{
    "input": {
        "task": "midi",
        "audio_url": "https://api.genaudius.studio/stems/vocals.wav"
    }
}
```

## Troubleshooting
- Ensure **FFmpeg** is available (included in the Docker image).
- For large files, increase the **timeout** settings in RunPod.
