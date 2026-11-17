"""Yeni fatura eşleştirmesini ve geçmişi bozmayan mali analiz kurallarını sınar."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from service_analysis import Services, period_from_note, ratio


class ServiceAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.services = Services(self.temp.name)
        source = {
            "years": [2025, 2026],
            "imported_date": "2026-11-17",
            "baseline_invoice_numbers": ["OLD001"],
            "rows": [
                {
                    "id": "excel-row-5",
                    "institution": "Sinerji",
                    "description": "Ekinoks",
                    "amounts": {"2025": "8320", "2026": "8320"},
                    "rates": {},
                    "total_increase": None,
                    "invoice_count": 10,
                    "service_type": "Bitti",
                    "note": "2025 Kasım ayında başladı. 2026 Ekim ayında bitti",
                }
            ],
        }
        Services.write(self.services.root / "increase-analysis.json", source)
        self.started = self.services.config()["started_at"]

    def doc(self, number="NEW001", amount="9000", status="approved", when="2026-11-18"):
        return {
            "id": number,
            "status": status,
            "created_at": self.started,
            "updated_at": self.started,
            "edited": {
                "seller": {"name": "Sinerji Bilgisayar"},
                "currency": "TRY",
                "invoice_number": number,
                "invoice_date": when,
                "items": [{"name": "Hizmet", "description": "Ekinoks hizmet bedeli"}],
                "totals": {"gross": amount},
            },
        }

    def row(self, docs):
        return self.services.analysis(docs)["rows"][0]

    def test_paid_on_upload_but_price_waits_for_approval(self):
        pending = self.doc(status="review")
        row = self.row([pending])
        self.assertEqual(row["invoice_count"], 11)
        self.assertTrue(row["history"][0]["paid"])
        self.assertIsNone(row["history"][0]["payment_date"])
        self.assertEqual(row["amounts"]["2026"], "8320")
        pending["status"] = "approved"
        row = self.row([pending])
        self.assertEqual(row["amounts"]["2026"], "9000")
        self.assertEqual(row["rates"]["2026"], "0.0817")

    def test_reference_and_duplicate_uploads_not_counted_twice(self):
        first = self.doc("OLD001")
        duplicate = deepcopy(first)
        duplicate["id"] = "second-upload"
        self.assertEqual(self.row([first, duplicate])["invoice_count"], 10)
        self.assertEqual(len(self.row([first, duplicate])["history"]), 1)
        first["status"] = "deleted"
        self.assertEqual(len(self.row([first])["history"]), 0)

    def test_old_pdf_does_not_replace_source_last_price(self):
        row = self.row([self.doc(when="2026-02-01", amount="5000")])
        self.assertEqual(row["amounts"]["2026"], "8320")

    def test_actual_invoice_date_orders_new_prices(self):
        a = self.doc("A", "10000", when="2027-05-01")
        b = self.doc("B", "9000", when="2027-02-01")
        self.assertEqual(self.row([a, b])["amounts"]["2027"], "10000")

    def test_existing_documents_excluded_unless_explicitly_linked(self):
        doc = self.doc()
        doc["created_at"] = "2020-01-01"
        self.assertEqual(self.row([doc])["invoice_count"], 10)
        doc["edited"]["service_id"] = "excel-row-5"
        self.assertEqual(self.row([doc])["invoice_count"], 11)

    def test_ambiguous_descriptions_require_selection(self):
        self.services.create({"description": "Protein TSS", "institution": "Sinerji"})
        record = self.doc()["edited"]
        record["items"][0]["description"] = "Ekinoks ve Protein TSS hizmet bedeli"
        match = self.services.match(record)
        self.assertIsNone(match["id"])
        self.assertEqual(match["method"], "ambiguous")

    def test_vendor_and_currency_are_separate(self):
        record = self.doc()["edited"]
        record["currency"] = "USD"
        self.assertIsNone(self.services.match(record)["id"])
        record["currency"] = "TRY"
        record["seller"]["name"] = "Başka firma"
        self.assertIsNone(self.services.match(record)["id"])
        record["service_id"] = "excel-row-5"
        record["currency"] = "USD"
        with self.assertRaises(ValueError):
            self.services.validate_link(record)

    def test_new_service_full_institution_and_latest_price(self):
        row = self.services.create(
            {"description": "Yazılım desteği", "institution": "ABC Bilişim Ltd"}
        )
        record = self.doc()["edited"]
        record["seller"]["name"] = "ABC Bilişim Ltd"
        record["items"][0]["description"] = "Yazılım desteği"
        self.assertEqual(self.services.match(record)["id"], row["id"])

    def test_source_period_precision_and_unknown_start(self):
        row = self.row([])
        self.assertEqual(row["start_period"], "2025-11")
        self.assertEqual(row["end_period"], "2026-10")
        self.assertEqual(row["lifecycle"], "ended")
        self.assertIsNone(period_from_note("Aylık hizmet", "BASLA"))
        self.assertIsNone(ratio("0", "10"))
        self.assertEqual(ratio("10", "10"), "0.0000")


if __name__ == "__main__":
    unittest.main()
