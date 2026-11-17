"""Ayrılmış fatura kümelerinde yeniden üretilebilir PaddleOCR deneyi."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

from extraction_service import image_record, merge_records, render_page
from invoice import extract


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def code_digest():
    """Deneyin hangi çıkarım koduyla yapıldığını kaydeder."""
    root = Path(__file__).resolve().parent
    paths = [
        root / name
        for name in (
            "extraction_service.py",
            "flexible_layout.py",
            "scan_invoice.py",
            "invoice.py",
            "document_notes.py",
            "identifier_check.py",
            "image_preprocessing.py",
            "ocr_backends.py",
        )
    ] + sorted((root / "lab_engines").glob("*.py"))
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def run(dataset, split, label):
    from lab_engines.paddle_reader import PaddleBackend

    manifest = json.loads((dataset / "manifest.json").read_text())
    if split == "holdout":
        freeze = json.loads((dataset / "freeze.json").read_text())
        if freeze["code_sha256"] != code_digest():
            raise ValueError(
                "Test öncesi sabitlenen çıkarım kodu değişmiş; bağımsız test çalıştırılmadı."
            )
    backend = PaddleBackend()
    recognize = backend.recognize
    cache = dataset / "ocr_cache"
    cache.mkdir(exist_ok=True)

    def cached_recognize(image):
        # OCR gözlemleri saklanır; farklı kırpma yeni anahtar üretir. Referans
        # değerler önbelleğe veya okuyucuya verilmez.
        key = hashlib.sha256(
            b"paddleocr-3.3.2-latin-v5-rgb\0"
            + str(image.size).encode()
            + image.tobytes()
        ).hexdigest()
        path = cache / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text())
        result = recognize(image)
        write_json(path, result)
        return result

    backend.recognize = cached_recognize
    summary = {
        "split": split,
        "label": label,
        "code_sha256": code_digest(),
        "independent_holdout": split == "holdout",
        "documents": [],
    }
    for entry in manifest["documents"]:
        if split != "regression" and entry["split"] != split:
            continue
        folder = dataset / "documents" / entry["id"]
        started = time.perf_counter()
        try:
            source = folder / "source.pdf"
            if hashlib.sha256(source.read_bytes()).hexdigest() != entry["sha256"]:
                raise ValueError("Kaynak belgenin özeti değişmiş.")
            pages = extract(source)
            images = [render_page(source, folder, i + 1) for i in range(len(pages))]
            result = merge_records([image_record(image, backend) for image in images])
            error = None
            write_json(dataset / "runs" / label / entry["id"] / "result.json", result)
        except Exception as exc:
            result = {}
            error = f"{type(exc).__name__}: {exc}"
        item = {
            "id": entry["id"],
            "filename": entry["filename"],
            "error": error,
            "seconds": round(time.perf_counter() - started, 3),
            "item_count": len(result.get("items", [])),
        }
        summary["documents"].append(item)
        write_json(dataset / "runs" / label / "summary.json", summary)
        print(json.dumps(item, ensure_ascii=False), flush=True)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument(
        "--split", choices=["development", "holdout", "regression"], required=True
    )
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    if not args.label.replace("-", "").replace("_", "").isalnum():
        parser.error("Deney adı yalnızca harf, sayı, tire ve alt çizgi içermeli.")
    run(args.dataset, args.split, args.label)
