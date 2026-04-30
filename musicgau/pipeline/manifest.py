from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Iterable

from musicgau.pipeline.schema import ClipMeta


def write_jsonl(path: Path, rows: Iterable[dict], gzip_compress: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if gzip_compress and not str(path).endswith(".gz"):
        path = path.with_suffix(path.suffix + ".gz")
    if gzip_compress:
        with gzip.open(str(path), "wt", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    else:
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


def clipmeta_to_audiocraft_row(cm: ClipMeta) -> dict:
    """
    AudioCraft datasets commonly expect at least a `path` plus text conditioning fields.
    We keep all metadata, but also provide `text` as a stable alias for conditioning.
    """
    base = cm.to_json()
    text = cm.description or ""
    base["text"] = text
    return base

