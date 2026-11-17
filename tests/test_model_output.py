"""Yeni modelde tek bozuk alan doğru okunan diğer alanları kaybettirmemeli."""

import unittest
from lab_engines.model_output import normalize_model_output


class ModelOutputTests(unittest.TestCase):
    def test_bad_field_does_not_discard_valid_product(self):
        result = normalize_model_output(
            {
                "invoice_number": "ABC0001",
                "invoice_date": "yanlış",
                "currency": "USD",
                "items": [
                    {
                        "name": "Disk",
                        "quantity": "4",
                        "unit_price": "700",
                        "vat_rate": "20",
                        "line_total": "2800",
                    }
                ],
                "totals": {"net": "2800", "vat": "560", "gross": "3360"},
            }
        )
        self.assertEqual(result["items"][0]["quantity"], "4")
        self.assertEqual(result["totals"]["gross"], "3360")
        self.assertIsNone(result["invoice_date"])
        self.assertEqual(result["invoice_number"], "ABC0001")

    def test_nan_is_never_a_money_value(self):
        result = normalize_model_output({"totals": {"net": "NaN"}})
        self.assertIsNone(result["totals"]["net"])
