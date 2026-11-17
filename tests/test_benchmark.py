"""Deney araçları üretim kayıtlarını veya test ayrımını bozmamalı."""

import json
from pathlib import Path
import tempfile
import unittest

from app import ROOT
from benchmark_report import publish
from benchmark_paddle import run


class BenchmarkTests(unittest.TestCase):
    def test_publish_rejects_production_root_and_children(self):
        for path in [ROOT / "data", ROOT / "data" / "benchmark"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                publish(Path("/unused"), {"documents": []}, path)

    def test_changed_code_is_rejected_before_holdout_inference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.json").write_text(json.dumps({"documents": []}))
            (root / "freeze.json").write_text(json.dumps({"code_sha256": "different"}))
            with self.assertRaises(ValueError):
                run(root, "holdout", "test")
