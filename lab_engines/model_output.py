"""Model çıktısını alan alan normalleştirir; tek bozuk alan bütün belgeyi silmez."""

from datetime import date
from decimal import Decimal, InvalidOperation
import re
from invoice import number, validate
from extraction_service import empty_record


def normalize_model_output(raw):
    if not isinstance(raw, dict):
        raise ValueError("Model fatura nesnesi üretmedi.")
    record = empty_record()
    record["issues"], record["checks"] = [], []

    def issue(field, value):
        record["issues"].append(
            {
                "code": "model_field_review",
                "detail": f"{field}: {value} değeri doğrulanmalı.",
            }
        )

    def text(value):
        return str(value).strip() or None if value is not None else None

    def numeric(field, value):
        value = text(value)
        if value is None:
            return None
        try:
            result = number(value) if "," in value else Decimal(value)
            if not result.is_finite() or abs(result) > Decimal("1e15"):
                raise ValueError()
            return str(result)
        except (ValueError, InvalidOperation):
            issue(field, value)
            return None

    seller = raw.get("seller") if isinstance(raw.get("seller"), dict) else {}
    record["seller"] = {
        key: text(seller.get(key)) for key in ("name", "tax_id", "address")
    }
    for key in ("invoice_number", "invoice_note", "currency"):
        record[key] = text(raw.get(key))
    if record["currency"] == "TL":
        record["currency"] = "TRY"
    if record["currency"] and not re.fullmatch("[A-Z]{3}", record["currency"]):
        issue("currency", record["currency"])
        record["currency"] = None
    if raw.get("invoice_date"):
        try:
            record["invoice_date"] = date.fromisoformat(
                str(raw["invoice_date"])
            ).isoformat()
        except ValueError:
            issue("invoice_date", raw["invoice_date"])
    totals = raw.get("totals") if isinstance(raw.get("totals"), dict) else {}
    record["totals"] = {
        key: numeric("totals." + key, totals.get(key)) for key in record["totals"]
    }
    items = raw.get("items", [])
    if not isinstance(items, list):
        items = []
        issue("items", "Liste üretilemedi")
    for i, row in enumerate(items):
        if not isinstance(row, dict):
            issue(f"items.{i}", row)
            continue
        item = {key: text(row.get(key)) for key in ("name", "description", "unit")}
        item.update(
            {
                key: numeric(f"items.{i}.{key}", row.get(key))
                for key in (
                    "quantity",
                    "unit_price",
                    "vat_rate",
                    "line_total",
                    "discount",
                )
            }
        )
        for key in ("price_basis", "total_basis"):
            item[key] = row.get(key) if row.get(key) in ("net", "gross") else "unknown"
        item["evidence"] = None
        record["items"].append(item)
        if "unknown" in (item["price_basis"], item["total_basis"]):
            record["issues"].append(
                {
                    "code": "ambiguous_tax_basis",
                    "detail": f"{i+1}. kalemin vergi esası doğrulanmalı.",
                }
            )
    return validate(record)
