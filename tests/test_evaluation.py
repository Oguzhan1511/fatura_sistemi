"""Değerlendirmenin harf hatalarını saklamadan ve ondalık biçime takılmadan ölçmesi gerekir."""
import unittest
from evaluate_invoices import compare


class EvaluationTests(unittest.TestCase):
    def test_identifier_mismatch_and_missing_rows_are_scored(self):
        expected={'invoice_number':'LAS001','items':[{'quantity':'1.0','unit_price':'700.00'}]}
        actual={'invoice_number':'L4S001','items':[]}
        checks={entry['field']:entry for entry in compare(expected,actual)}
        self.assertFalse(checks['invoice_number']['match'])
        self.assertFalse(checks['items.0.quantity']['match'])
        self.assertFalse(checks['item_count']['match'])

    def test_decimal_format_difference_is_not_an_extraction_error(self):
        expected={'items':[{'quantity':'1.0','unit_price':'700.00'}]}
        actual={'items':[{'quantity':'1','unit_price':'700'}]}
        self.assertTrue(all(entry['match'] for entry in compare(expected,actual)))
