"""Kullanıcı onaylı kayıtları referans alarak yerel çıkarım başarısını ölçer.

Varsayılan mod saklanan ilk okumayı ölçer; güncel motor için --rerun kullanılır.
Sonuçlar kayıtları değiştirmez. Bu örnekler geliştirmede görüldüğü için bağımsız
başarı testi değildir; yeni tedarikçilerden ayrılmış bir test kümesi de gerekir.
"""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import time


FIELDS = ('seller.name', 'invoice_number', 'invoice_date', 'currency',
          'totals.net', 'totals.vat', 'totals.gross', 'totals.payable', 'totals.withholding')
ITEM_FIELDS = ('name', 'description', 'quantity', 'unit', 'unit_price', 'vat_rate', 'line_total')
NUMERIC = {'net', 'vat', 'gross', 'payable', 'withholding', 'quantity', 'unit_price', 'vat_rate', 'line_total'}


def value_at(record, path):
    value = record
    for key in path.split('.'):
        value = value.get(key) if isinstance(value, dict) else None
    return value


def compare(expected, actual):
    """Eksik referans alanı puanlamaz; sayı biçimi farkını hataya dönüştürmez."""
    checks = []
    pairs = [(field, value_at(expected, field), value_at(actual, field)) for field in FIELDS]
    for i, item in enumerate(expected.get('items', [])):
        observed = actual.get('items', [])
        observed = observed[i] if i < len(observed) else {}
        pairs.extend((f'items.{i}.{field}', item.get(field), observed.get(field)) for field in ITEM_FIELDS)
    for field, expected_value, actual_value in pairs:
        if expected_value is None or expected_value == '':
            continue
        match = expected_value == actual_value
        if actual_value is not None and field.split('.')[-1] in NUMERIC:
            try:
                match = Decimal(str(expected_value)) == Decimal(str(actual_value))
            except Exception:
                match = False
        checks.append({'field': field, 'expected': expected_value, 'actual': actual_value, 'match': match})
    expected_count, actual_count = len(expected.get('items', [])), len(actual.get('items', []))
    checks.append({'field': 'item_count', 'expected': expected_count, 'actual': actual_count, 'match': expected_count == actual_count})
    return checks


def evaluate(data_root, output, rerun=False):
    # Store başlangıcındaki işlem durumlarını değiştirmemek için veritabanı salt okunur açılır.
    import sqlite3
    db = sqlite3.connect(f'file:{(Path(data_root)/"invoices.sqlite3").resolve()}?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    rows = db.execute("SELECT * FROM documents WHERE status='approved' ORDER BY created_at").fetchall()
    pending = db.execute("SELECT COUNT(*) FROM documents WHERE status='review'").fetchone()[0]
    db.close()
    results = []
    for row in rows:
        expected = json.loads(row['edited_json'])
        source = Path(data_root)/'files'/row['id']/'source'
        start = time.perf_counter()
        error = None
        try:
            if rerun:
                from extraction_service import analyze
                actual = analyze(source, row['mime'])
            else:
                actual = json.loads(row['original_json'] or '{}')
        except Exception as exc:
            error = str(exc)
            actual = {}
        checks = compare(expected, actual)
        results.append({'id': row['id'], 'filename': row['filename'],
                        'supplier_group': expected.get('seller', {}).get('name'),
                        'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                        'elapsed_seconds': round(time.perf_counter()-start, 3),
                        'metrics': actual.get('metrics'), 'error': error,
                        'all_fields_match': all(check['match'] for check in checks), 'checks': checks})
        print(f"{row['filename']}: {sum(c['match'] for c in checks)}/{len(checks)} alan", flush=True)
    checks = [check for result in results for check in result['checks']]
    summary = {'mode': 'current_engine' if rerun else 'stored_initial_readings',
               'documents': len(results), 'matching_fields': sum(c['match'] for c in checks),
               'scored_fields': len(checks), 'fully_matching_documents': sum(r['all_fields_match'] for r in results),
               'independent_holdout': False, 'unscored_review_documents': pending,
               'selection_warning': 'Yalnızca onaylı kayıtlar puanlanır; başarısız/incelemedeki belgeler bu skora dahil değildir.',
               'reference': 'Kullanıcı onaylı kayıtlar; bağımsız elle doğrulama garantisi değildir.'}
    report = {'summary': summary, 'documents': results}
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=Path(__file__).resolve().parent/'data')
    parser.add_argument('--output', type=Path, default=Path('data/evaluation/baseline.json'))
    parser.add_argument('--rerun', action='store_true')
    args = parser.parse_args()
    evaluate(args.data_dir, args.output, args.rerun)
