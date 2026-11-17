"""Hizmet eşleştirme ve Excel başlangıcına eklenen yeni fatura analizleri."""

from copy import deepcopy
from decimal import Decimal, localcontext
import difflib
import json
from pathlib import Path
import re
import threading
import uuid

from document_notes import normalized
from storage import now

LOCK = threading.RLock()


def words(text):
    return " ".join(re.findall(r"[A-Z0-9]+", normalized(text or "")))


class Services:
    def __init__(self, root):
        self.root = Path(root) / "reference"
        self.root.mkdir(parents=True, exist_ok=True)
        self.settings = self.root / "service-tracking.json"
        with LOCK:
            if not self.settings.exists():
                self.write(self.settings, {"started_at": now(), "custom_rows": []})

    @staticmethod
    def write(path, value):
        temporary = path.with_suffix(".pending")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(path)

    def reference(self):
        path = self.root / "increase-analysis.json"
        return (
            json.loads(path.read_text()) if path.exists() else {"rows": [], "years": []}
        )

    def config(self):
        return json.loads(self.settings.read_text())

    def rows(self):
        return self.reference()["rows"] + self.config()["custom_rows"]

    def create(self, payload):
        name = payload.get("description")
        institution = payload.get("institution")
        currency = payload.get("currency", "TRY")
        if not isinstance(name, str) or not name.strip() or len(name) > 300:
            raise ValueError("Hizmet adı 1–300 karakter olmalı.")
        if (
            not isinstance(institution, str)
            or not institution.strip()
            or len(institution) > 300
        ):
            raise ValueError("Kurum adı gerekli.")
        if not isinstance(currency, str) or not re.fullmatch("[A-Z]{3}", currency):
            raise ValueError("Para birimi TRY, USD gibi üç harfli kod olmalı.")
        with LOCK:
            config = self.config()
            for row in self.rows():
                if (
                    words(row["description"]) == words(name)
                    and words(row.get("institution")) == words(institution)
                    and row.get("currency", "TRY") == currency
                ):
                    return row
            row = {
                "id": "service-" + uuid.uuid4().hex,
                "description": name.strip(),
                "institution": institution.strip(),
                "currency": currency,
                "amounts": {},
                "rates": {},
                "total_increase": None,
                "invoice_count": 0,
                "unit_price": None,
                "service_type": None,
                "single_date": None,
                "note": None,
            }
            config["custom_rows"].append(row)
            self.write(self.settings, config)
        return row

    def match(self, record, rows=None):
        rows = self.rows() if rows is None else rows
        manual = record.get("service_id")
        if manual:
            found = next((r for r in rows if r["id"] == manual), None)
            return {
                "id": manual if found else None,
                "method": "manual",
                "candidates": [],
            }
        vendor = words(record.get("seller", {}).get("name"))
        currency = record.get("currency")
        eligible = [
            r
            for r in rows
            if currency == r.get("currency", "TRY")
            and (
                (" " + words(r.get("institution")) + " ") in (" " + vendor + " ")
                or any(
                    token == words(r.get("institution"))
                    or difflib.SequenceMatcher(
                        None, token, words(r.get("institution"))
                    ).ratio()
                    >= 0.85
                    for token in vendor.split()
                )
            )
        ]
        # Fatura açıklaması önceliklidir; kalem adları ikinci kaynaktır.
        descriptions = " ".join(
            i.get("description") or "" for i in record.get("items", [])
        )
        texts = [
            descriptions,
            " ".join(i.get("name") or "" for i in record.get("items", [])),
            record.get("invoice_note") or "",
        ]
        for text in texts:
            haystack = " " + words(text) + " "
            matches = []
            for row in eligible:
                aliases = [row["description"]] + row.get("aliases", [])
                if words(row["description"]) == "PACS HIZMETI":
                    aliases += ["Radyoloji Görüntüleme", "PACS"]
                if words(row["description"]) == "PROTEIN TSS":
                    aliases += ["TSS Protein"]
                for alias in aliases:
                    phrase = " " + words(alias) + " "
                    if phrase.strip():
                        start = haystack.find(phrase)
                        if start >= 0:
                            matches.append((row["id"], start, start + len(phrase)))
            # Özel Sigorta Kapsamlı gibi iç içe adlarda tam ad tercih edilir;
            # bağımsız iki hizmet adı varsa tutardan tahmin yapılmaz.
            matches = [
                m
                for m in matches
                if not any(
                    other[0] != m[0]
                    and other[1] <= m[1]
                    and other[2] >= m[2]
                    and other[2] - other[1] > m[2] - m[1]
                    for other in matches
                )
            ]
            ids = sorted({m[0] for m in matches})
            if ids:
                return {
                    "id": ids[0] if len(ids) == 1 else None,
                    "method": "automatic" if len(ids) == 1 else "ambiguous",
                    "candidates": ids,
                }
        return {"id": None, "method": "unmatched", "candidates": []}

    def validate_link(self, record):
        service_id = record.get("service_id")
        if service_id is None:
            return
        row = next((r for r in self.rows() if r["id"] == service_id), None)
        if row is None:
            raise ValueError("Seçilen hizmet bulunamadı.")
        if record.get("currency") and row.get("currency", "TRY") != record["currency"]:
            raise ValueError("Faturanın para birimi seçilen hizmetle aynı olmalı.")

    def analysis(self, documents):
        reference = self.reference()
        config = self.config()
        rows = deepcopy(self.rows())
        cutoff = reference.get(
            "baseline_as_of", reference.get("imported_date", "0000-01-01")
        )
        baseline_ids = {
            words(number) for number in reference.get("baseline_invoice_numbers", [])
        }
        histories = {r["id"]: {} for r in rows}
        unmatched = []
        for doc in documents:
            if doc["status"] in ("deleted", "processing", "duplicate"):
                continue
            record = doc.get("edited") or {}
            if doc["created_at"] < config["started_at"] and not record.get(
                "service_id"
            ):
                continue
            matched = self.match(record, rows)
            if not matched["id"]:
                if doc["status"] != "processing":
                    unmatched.append(doc["id"])
                continue
            service = next((r for r in rows if r["id"] == matched["id"]), None)
            if service is None or record.get("currency") != service.get(
                "currency", "TRY"
            ):
                continue
            number = record.get("invoice_number")
            key = words(number) if number else doc["id"]
            entry = {
                "id": doc["id"],
                "invoice_number": number,
                "invoice_date": record.get("invoice_date"),
                "gross": record.get("totals", {}).get("gross"),
                "currency": record.get("currency"),
                "status": doc["status"],
                "paid": True,
                "payment_date": None,
                "in_reference": words(number) in baseline_ids
                and service["id"].startswith("excel-row-"),
                "updated_at": doc["updated_at"],
            }
            previous = histories[service["id"]].get(key)
            if previous is None or (
                entry["status"] == "approved",
                entry["updated_at"],
            ) > (previous["status"] == "approved", previous["updated_at"]):
                histories[service["id"]][key] = entry
        years = set(reference.get("years", []))
        for row in rows:
            history = sorted(
                histories[row["id"]].values(),
                key=lambda h: (h["invoice_date"] or "", h["updated_at"]),
            )
            row["history"] = history
            row["reference_invoice_count"] = row.get("invoice_count")
            added = [h for h in history if not h["in_reference"]]
            row["invoice_count"] = (row.get("invoice_count") or 0) + len(added)
            row["new_invoice_count"] = len(added)
            row["pending_count"] = sum(h["status"] != "approved" for h in history)
            changed = set()
            baseline_years = {y for y, v in row["amounts"].items() if v is not None}
            for item in history:
                if (
                    item["status"] != "approved"
                    or item["gross"] is None
                    or not item["invoice_date"]
                ):
                    continue
                year = item["invoice_date"][:4]
                # Eski tarihli PDF, Excel'in daha güncel yıl sonu bedelini ezmez.
                if year in baseline_years and item["invoice_date"] <= cutoff:
                    continue
                row["amounts"][year] = item["gross"]
                changed.add(int(year))
                years.add(int(year))
            for year in changed | {y + 1 for y in changed}:
                a, b = row["amounts"].get(str(year - 1)), row["amounts"].get(str(year))
                row["rates"][str(year)] = ratio(a, b)
            series = [
                {"year": int(y), "amount": value}
                for y, value in sorted(row["amounts"].items())
                if value is not None
            ]
            if changed and len(series) > 1:
                row["total_increase"] = ratio(series[0]["amount"], series[-1]["amount"])
            row["series"] = series
            row["currency"] = row.get("currency", "TRY")
            row["start_period"] = period_from_note(row.get("note"), "BASLA")
            row["end_period"] = period_from_note(row.get("note"), "BIT")
            row["lifecycle"] = (
                "ended" if row.get("service_type") == "Bitti" else "unknown"
            )
            row["first_recorded_invoice"] = (
                history[0]["invoice_date"] if history else None
            )
            row["price_change"] = (
                ratio(series[0]["amount"], series[-1]["amount"])
                if len(series) > 1
                else None
            )
        return {
            **reference,
            "rows": rows,
            "years": sorted(years),
            "tracking_started_at": config["started_at"],
            "unmatched_document_ids": unmatched,
            "payment_rule": "Yüklenen fatura ödenmiştir; ödeme tarihi tahmin edilmez.",
        }


def ratio(previous, current):
    if previous is None or current is None or Decimal(previous) == 0:
        return None
    with localcontext() as context:
        context.prec = 40
        return str(
            ((Decimal(current) - Decimal(previous)) / Decimal(previous)).quantize(
                Decimal(".0001")
            )
        )


def period_from_note(note, action):
    months = [
        "OCAK",
        "SUBAT",
        "MART",
        "NISAN",
        "MAYIS",
        "HAZIRAN",
        "TEMMUZ",
        "AGUSTOS",
        "EYLUL",
        "EKIM",
        "KASIM",
        "ARALIK",
    ]
    match = re.search(
        r"(20\d{2})\s+(" + "|".join(months) + r")\s+(?:AYINDA\s+)?" + action,
        words(note),
    )
    return f"{match[1]}-{months.index(match[2])+1:02d}" if match else None
