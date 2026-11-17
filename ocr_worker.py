"""Ağır modelleri ayrı süreçte çalıştırır; iş bitince model belleği bırakılır."""

import argparse
import json
import os
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("HF_HOME", str(ROOT / "lab_models/hf"))
os.environ.setdefault("PADDLE_PDX_CACHE_HOME", str(ROOT / "lab_models/paddlex"))
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def run(reader, source, mime, experimental=False):
    from extraction_service import image_record, render_page, merge_records
    from invoice import extract
    from metrics import peak_rss_bytes

    started = time.perf_counter()
    if mime == "application/pdf":
        pages = extract(source)
        if len(pages) > 30:
            raise ValueError("En fazla 30 sayfa yüklenebilir.")
        images = [render_page(source, source.parent, i + 1) for i in range(len(pages))]
    else:
        images = [source.parent / "page-1.png"]
    if reader == "paddle":
        from lab_engines.paddle_reader import PaddleBackend

        backend = PaddleBackend()
        records = [image_record(image, backend) for image in images]
    elif reader == "qwen":
        from lab_engines.qwen_reader import QwenReader

        backend = QwenReader()
        records = [backend(image) for image in images]
    else:
        raise ValueError("Bilinmeyen okuyucu.")
    result = merge_records(records)
    result["metrics"] = {
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "process_peak_rss_bytes": peak_rss_bytes(),
    }
    result["reader"] = reader
    if experimental:
        result["issues"].append(
            {
                "code": "experimental_reader",
                "detail": "Deneysel model sonucu; tüm kritik alanları kaynak belgeyle doğrulayın.",
            }
        )
    result["needs_review"] = True
    return result


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
