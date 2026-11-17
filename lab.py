"""ERP'den ayrı veritabanı ve yükleme alanıyla yerel fatura okuma laboratuvarı."""

import argparse
import json
from pathlib import Path
import threading
import subprocess
import shutil
import uuid
import re
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from app import Application, Handler, ROOT
from storage import now, Store
from extraction_service import empty_record

READER_NAMES = {
    "prototype": "Mevcut prototip",
    "paddle": "PaddleOCR · Türkçe PP-OCRv5",
    "qwen": "Qwen3-VL-2B · 4 bit görsel model",
}


def reader_status():
    path = ROOT / "lab_models/status.json"
    status = json.loads(path.read_text()) if path.exists() else {}
    python = (
        ROOT / ".venv-lab" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    )
    return [
        {
            "id": key,
            "name": name,
            "available": key == "prototype"
            or (
                status.get(key, {}).get("ready", False)
                and python.is_file()
                and (key != "qwen" or sys.platform == "darwin")
            ),
            "details": status.get(key, {}),
        }
        for key, name in READER_NAMES.items()
    ]


class LabStore(Store):
    def __init__(self, root, context, recover_processing=True):
        # Aynı PDF'nin farklı modellerle karşılaştırılması laboratuvarda serbesttir.
        super().__init__(
            root, recover_processing=recover_processing, prevent_duplicates=False
        )
        self.context = context
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS lab_runs(document_id TEXT PRIMARY KEY,reader TEXT NOT NULL)"
            )

    def create(self, identifier, filename, mime):
        reader = getattr(self.context, "reader", "prototype")
        filename = re.sub(r"^\[(?:Prototip|PaddleOCR|Qwen3-VL)\]\s*", "", filename)
        prefix = {"prototype": "Prototip", "paddle": "PaddleOCR", "qwen": "Qwen3-VL"}[
            reader
        ]
        doc = super().create(identifier, f"[{prefix}] {filename}", mime)
        with self.connect() as db:
            db.execute(
                "INSERT INTO lab_runs(document_id,reader) VALUES(?,?)",
                (identifier, reader),
            )
        return doc

    def reader(self, identifier):
        with self.connect() as db:
            row = db.execute(
                "SELECT reader FROM lab_runs WHERE document_id=?", (identifier,)
            ).fetchone()
        return row[0] if row else "prototype"


class LabApplication(Application):
    def __init__(self, root):
        super().__init__(root, reader="prototype")
        self.executor.shutdown(wait=True)
        self.executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="lab-model"
        )
        self.upload_context = threading.local()
        self.store = LabStore(root, self.upload_context)

    def process(self, identifier):
        reader = self.store.reader(identifier)
        if reader == "prototype":
            return super().process(identifier)
        doc = self.store.get(identifier)
        output = self.store.file(identifier).parent / "model-result.json"
        log = self.store.file(identifier).parent / "model-run.log"
        try:
            python = (
                ROOT
                / ".venv-lab"
                / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            )
            with log.open("w") as stream:
                subprocess.run(
                    [
                        str(python),
                        str(ROOT / "lab_worker.py"),
                        "--reader",
                        reader,
                        "--source",
                        str(self.store.file(identifier)),
                        "--mime",
                        doc["mime"],
                        "--output",
                        str(output),
                    ],
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    check=True,
                    timeout=900,
                )
            self.store.analyzed(
                identifier, json.loads(output.read_text(encoding="utf-8"))
            )
        except Exception:
            self.store.analyzed(
                identifier,
                empty_record(),
                f"{READER_NAMES[reader]} denemesi tamamlanamadı. Başka bir motor seçebilir veya alanları elle doldurabilirsiniz.",
            )


class LabHandler(Handler):
    def get(self):
        path = urlparse(self.path).path
        if path in ("/", "/lab.js", "/lab.css"):
            name = "index.html" if path == "/" else path[1:]
            file = ROOT / "lab_web" / name
            mime = {
                "index.html": "text/html",
                "lab.js": "application/javascript",
                "lab.css": "text/css",
            }[name]
            return self.send(200, file.read_bytes(), mime + "; charset=utf-8")
        if path == "/api/lab":
            with self.app.store.connect() as db:
                feedback = [
                    dict(row)
                    for row in db.execute(
                        "SELECT f.* FROM lab_feedback f JOIN documents d ON d.id=f.document_id WHERE d.status!='deleted'"
                    )
                ]
            return self.send(
                200,
                {
                    "environment": "lab",
                    "reader": "Seçilebilir yerel test motorları",
                    "models": reader_status(),
                    "readers_by_document": {
                        doc["id"]: self.app.store.reader(doc["id"])
                        for doc in self.app.store.list()
                    },
                    "feedback": feedback,
                },
            )
        return super().get()

    def post(self):
        parsed = urlparse(self.path)
        parts = parsed.path.strip("/").split("/")
        if parsed.path == "/api/uploads":
            reader = parse_qs(parsed.query).get("reader", ["prototype"])[0]
            self.select_reader(reader)
            try:
                return super().post()
            finally:
                self.app.upload_context.reader = "prototype"
        if len(parts) == 4 and parts[:2] == ["api", "lab"] and parts[3] == "run":
            source_doc = self.document(parts[2])
            payload = json.loads(self.body())
            reader = payload.get("reader")
            self.select_reader(reader)
            identifier = uuid.uuid4().hex
            directory = self.app.store.root / "files" / identifier
            directory.mkdir(parents=True)
            shutil.copy2(self.app.store.file(source_doc["id"]), directory / "source")
            if source_doc["mime"] != "application/pdf":
                shutil.copy2(
                    self.app.store.file(source_doc["id"]).parent / "page-1.png",
                    directory / "page-1.png",
                )
            try:
                doc = self.app.store.create(
                    identifier, source_doc["filename"], source_doc["mime"]
                )
            finally:
                self.app.upload_context.reader = "prototype"
            self.app.executor.submit(self.app.process, identifier)
            return self.send(201, doc)
        if len(parts) == 4 and parts[:2] == ["api", "lab"] and parts[3] == "feedback":
            doc = self.document(parts[2])
            payload = json.loads(self.body())
            rating = payload.get("rating")
            notes = payload.get("notes", "")
            if rating not in ("pass", "partial", "fail"):
                raise ValueError(
                    "Başarılı, kısmen doğru veya hatalı seçeneklerinden birini seçin."
                )
            if not isinstance(notes, str) or len(notes) > 10000:
                raise ValueError("Test notu en fazla 10.000 karakter olabilir.")
            if doc["status"] == "processing":
                raise ValueError("Önce okumanın tamamlanmasını bekleyin.")
            with self.app.store.connect() as db:
                db.execute(
                    """INSERT INTO lab_feedback(document_id,rating,notes,updated_at,reader)
                    VALUES(?,?,?,?,?) ON CONFLICT(document_id) DO UPDATE SET rating=excluded.rating,
                    notes=excluded.notes,updated_at=excluded.updated_at,reader=excluded.reader""",
                    (
                        doc["id"],
                        rating,
                        notes.strip(),
                        now(),
                        self.app.store.reader(doc["id"]),
                    ),
                )
            return self.send(200, {"saved": True})
        return super().post()

    def select_reader(self, reader):
        if not any(
            model["id"] == reader and model["available"] for model in reader_status()
        ):
            raise ValueError("Seçilen motor hazır değil veya bulunamadı.")
        self.app.upload_context.reader = reader


def create_lab_server(port=8767, data_root=None):
    root = (Path(data_root) if data_root else ROOT / "lab_data").resolve()
    production = (ROOT / "data").resolve()
    if root == production or root.is_relative_to(production):
        raise ValueError("Test ortamı ERP veri klasörünü kullanamaz.")
    app = LabApplication(root)
    with app.store.connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS lab_feedback (
            document_id TEXT PRIMARY KEY, rating TEXT NOT NULL, notes TEXT NOT NULL,
            updated_at TEXT NOT NULL, reader TEXT NOT NULL)""")
    server = ThreadingHTTPServer(("127.0.0.1", port), LabHandler)
    server.application = app
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "lab_data")
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()
    server = create_lab_server(args.port, args.data_dir)
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"Okuma laboratuvarı: {url}", flush=True)
    if args.open:
        import webbrowser

        threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        server.application.executor.shutdown(wait=True)
