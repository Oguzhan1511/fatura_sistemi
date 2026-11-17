"""Laboratuvar giriş noktası; ana sistemle aynı yerel model işçisini kullanır."""

import argparse
import json
from pathlib import Path

from ocr_worker import run as run_model


def run(reader, source, mime):
    return run_model(reader, source, mime, experimental=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reader", choices=["paddle", "qwen"], required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--mime", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.reader, args.source, args.mime)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
