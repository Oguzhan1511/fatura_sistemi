"""Laboratuvar yanlışlıkla ERP veri klasörüyle başlatılamamalıdır."""

import unittest
from app import ROOT
from lab import create_lab_server


class LabTests(unittest.TestCase):
    def test_benchmark_import_does_not_interrupt_processing_documents(self):
        import tempfile
        import threading
        from lab import LabStore

        with tempfile.TemporaryDirectory() as directory:
            store = LabStore(directory, threading.local())
            store.create("c" * 32, "devam-eden.pdf", "application/pdf")
            imported = LabStore(directory, threading.local(), recover_processing=False)
            self.assertEqual(imported.get("c" * 32)["status"], "processing")

    def test_production_data_directory_rejected_before_server_start(self):
        for root in [ROOT / "data", ROOT / "data" / "lab"]:
            with self.subTest(path=root), self.assertRaises(ValueError):
                create_lab_server(0, root)

    def test_reader_choice_is_saved_per_document(self):
        import tempfile
        import threading
        from lab import LabStore

        with tempfile.TemporaryDirectory() as directory:
            context = threading.local()
            store = LabStore(directory, context)
            context.reader = "paddle"
            doc = store.create("a" * 32, "ornek.pdf", "application/pdf")
            context.reader = "qwen"
            store.create("b" * 32, "ornek.pdf", "application/pdf")
            self.assertEqual(store.reader(doc["id"]), "paddle")
            self.assertEqual(store.reader("b" * 32), "qwen")
            self.assertTrue(doc["filename"].startswith("[PaddleOCR]"))

    def test_models_are_not_advertised_as_ready_without_status(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from lab import reader_status

        with tempfile.TemporaryDirectory() as directory, patch(
            "lab.ROOT", Path(directory)
        ):
            models = {entry["id"]: entry["available"] for entry in reader_status()}
        self.assertEqual(models, {"prototype": True, "paddle": False, "qwen": False})
