"""Görsel referansları ölçer; deney sonuçlarını onay vermeden laboratuvara aktarır."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import threading
import uuid

from benchmark_paddle import code_digest, write_json
from evaluate_invoices import compare


def evaluate(dataset):
    manifest = json.loads((dataset / "manifest.json").read_text())
    references = json.loads((dataset / "references.json").read_text())
    frozen = json.loads((dataset / "freeze.json").read_text())
    if code_digest() != frozen["code_sha256"]:
        raise ValueError("Çıkarım kodu sabit deney sürümüyle eşleşmiyor.")
    development_groups = {
        references[d["id"]]["invoice_group"]
        for d in manifest["documents"]
        if d["split"] == "development"
    }
    development_suppliers = {
        references[d["id"]]["supplier_group"]
        for d in manifest["documents"]
        if d["split"] == "development"
    }
    documents = []
    for entry in manifest["documents"]:
        reference = references[entry["id"]]
        label = "release" if entry["split"] == "development" else "holdout"
        summary = json.loads((dataset / "runs" / label / "summary.json").read_text())
        if summary["code_sha256"] != frozen["code_sha256"]:
            raise ValueError(f"{label}: deney sürümü eşleşmiyor.")
        result_path = dataset / "runs" / label / entry["id"] / "result.json"
        actual = json.loads(result_path.read_text()) if result_path.exists() else {}
        checks = compare(reference["record"], actual)
        document = {
            **entry,
            "run": label,
            "reference": reference,
            "checks": checks,
            "all_scored_match": all(c["match"] for c in checks),
            "new_invoice_in_holdout": entry["split"] == "holdout"
            and reference["invoice_group"] not in development_groups,
            "new_supplier_in_holdout": entry["split"] == "holdout"
            and reference["supplier_group"] not in development_suppliers,
        }
        if entry["split"] == "development":
            baseline = json.loads(
                (dataset / "runs/baseline" / entry["id"] / "result.json").read_text()
            )
            document["baseline_checks"] = compare(reference["record"], baseline)
        documents.append(document)
    report = {
        "code_sha256": frozen["code_sha256"],
        "documents": documents,
        "summary": {},
    }
    for split in ["development", "holdout"]:
        subset = [d for d in documents if d["split"] == split]
        checks = [c for d in subset for c in d["checks"]]
        report["summary"][split] = {
            "pdfs": len(subset),
            "matching_scored_fields": sum(c["match"] for c in checks),
            "scored_fields": len(checks),
            "all_scored_match": sum(d["all_scored_match"] for d in subset),
        }
    groups = Counter(d["reference"]["invoice_group"] for d in documents)
    report["summary"]["unique_invoices"] = len(groups)
    report["summary"]["suppliers"] = len(
        {d["reference"]["supplier_group"] for d in documents}
    )
    report["summary"]["duplicate_scans"] = sum(count - 1 for count in groups.values())
    write_json(dataset / "report.json", report)
    return report


def publish(dataset, report, lab_root):
    from lab import LabStore

    production = (Path(__file__).resolve().parent / "data").resolve()
    if Path(lab_root).resolve().is_relative_to(production):
        raise ValueError("Deney sonuçları ERP veri klasörüne aktarılamaz.")

    # Çalışan uygulamanın işlemleri kesilmez. Referanslar onaylı finansal kayıt
    # yapılmaz; yalnızca gerçekten üretilmiş OCR sonucu incelemeye açılır.
    context = threading.local()
    context.reader = "paddle"
    store = LabStore(lab_root, context, recover_processing=False)
    index_path = dataset / "published.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {}
    for doc in report["documents"]:
        if doc["id"] in index and store.get(index[doc["id"]]):
            continue
        source = dataset / "documents" / doc["id"] / "source.pdf"
        if hashlib.sha256(source.read_bytes()).hexdigest() != doc["sha256"]:
            raise ValueError("Aktarım kaynağı değişmiş.")
        identifier = uuid.uuid4().hex
        folder = store.root / "files" / identifier
        folder.mkdir(parents=True)
        shutil.copy2(source, folder / "source")
        for page in (source.parent).glob("page-*.png"):
            shutil.copy2(page, folder / page.name)
        result = json.loads(
            (dataset / "runs" / doc["run"] / doc["id"] / "result.json").read_text()
        )
        result["issues"].append(
            {
                "code": "benchmark_review",
                "detail": f"Deney {doc['id']}: referans karşılaştırması raporda; kullanıcı onayı verilmedi.",
            }
        )
        result["needs_review"] = True
        store.create(
            identifier, f"Deney {doc['id']} · {doc['filename']}", "application/pdf"
        )
        store.analyzed(identifier, result)
        index[doc["id"]] = identifier
        write_json(index_path, index)
    return index


def markdown(dataset, report, published):
    summary = report["summary"]
    lines = [
        "# PaddleOCR fatura deneyi — 16 Kasım 2026",
        "",
        f"14 PDF, {summary['unique_invoices']} farklı fatura, {summary['suppliers']} firma. "
        f"{summary['duplicate_scans']} PDF aynı faturanın farklı taramasıdır.",
        "",
        "## Ölçüm kapsamı",
        "",
        "Numara, tarih, para birimi, kalem sayısı, miktar, birim fiyat, KDV oranı, satır tutarı ve net/KDV/brüt/ödenecek/tevkifat toplamları kontrol edildi. "
        "Ürün/satıcı metinleri, açıklama, birim ve notlar bu sayısal başarı hesabına dahil değildir. "
        "Boş veya görselden kesin doğrulanamayan referans alanları puanlanmaz. "
        "Referanslar kaynak görsellerden elle çıkarılmıştır; kullanıcı onayı değildir. "
        "Bu ölçüm bütün faturanın veya her yeni düzenin hatasız okunduğu anlamına gelmez.",
        "",
        "## Sonuç",
        "",
        "| Grup | PDF | Eşleşen alan | Puanlanan alanları eşleşen PDF |",
        "|---|---:|---:|---:|",
    ]
    for split, title in [("development", "Geliştirme"), ("holdout", "Ayrılan test")]:
        s = summary[split]
        lines.append(
            f"| {title} | {s['pdfs']} | {s['matching_scored_fields']}/{s['scored_fields']} | {s['all_scored_match']}/{s['pdfs']} |"
        )
    new = [d for d in report["documents"] if d["new_invoice_in_holdout"]]
    unseen = [d for d in report["documents"] if d["new_supplier_in_holdout"]]
    lines += [
        "",
        f"Testte gerçekten yeni fatura: {sum(d['all_scored_match'] for d in new)}/{len(new)} eşleşti. "
        f"Yeni firma örneği: {sum(d['all_scored_match'] for d in unseen)}/{len(unseen)} eşleşti. "
        "Dolayısıyla farklı firmalara genelleme kanıtlanmış değildir.",
        "",
        "## Belge bazında",
        "",
        "| Belge | Grup / firma | Alanlar | Kalan hata veya sınır | İncele |",
        "|---|---|---:|---|---|",
    ]
    for doc in report["documents"]:
        bad = [
            f"{c['field']}: beklenen {c['expected']}, okunan {c['actual']}"
            for c in doc["checks"]
            if not c["match"]
        ]
        ref = doc["reference"]
        if ref.get("reference_uncertainty"):
            bad.append(ref["reference_uncertainty"])
        if ref.get("unsupported_fields"):
            bad.append(
                "Özel iletişim vergisi ortak şemada ayrı alan olarak desteklenmiyor; toplam kontrolü eksik kalabilir."
            )
        group = "Geliştirme" if doc["split"] == "development" else "Test"
        link = (
            f"[Aç](http://127.0.0.1:8767/#document/{published[doc['id']]})"
            if doc["id"] in published
            else "—"
        )
        lines.append(
            f"| {doc['id']} | {group} / {ref['supplier_group']} | {sum(c['match'] for c in doc['checks'])}/{len(doc['checks'])} | {'; '.join(bad) or 'Puanlanan alanlar eşleşti; metin alanları ayrıca kontrol edilmeli.'} | {link} |"
        )
    baseline = [c for d in report["documents"] for c in d.get("baseline_checks", [])]
    lines += [
        "",
        "## Geliştirme ve tekrar üretim",
        "",
        f"Geliştirme başlangıcı: {sum(c['match'] for c in baseline)}/{len(baseline)} alan. "
        "Küçük miktarlar için ek yerel okuma, para alanında açık binlik ayıraç onarımı ve doğrudan etiketli tevkifat okuması eklendi. "
        "Tutar veya miktar hesaplanıp kaynak yerine yazılmadı. Yardımcı OCR düşük güvenli olabilir; sonuçlar onay bekler.",
        "",
        "O/0 belirsizliği bulunan F01, F07 ve F14 numaraları kullanıcı tarafından teyit edilmelidir. "
        "F01 ve F14 miktarları ayrıca kontrol edilmelidir. F14 ek vergi şeması desteği gerektirir.",
        "",
        "Ayrım manifest.json içinde OCR öncesinde sabitlendi. Test çıktısı görüldükten sonra çıkarım kodu değiştirilmedi. "
        "freeze.json ile her deneyin kod özeti denetlenir. OCR önbelleği sadece görsel gözlemler içerir, referansları içermez. "
        "Önbellekli tekrar süreleri yeni faturanın işlem süresi değildir.",
        "",
        "```sh",
        "python benchmark_paddle.py --dataset lab_benchmarks/2026-11-16 --split development --label tekrar",
        "python benchmark_paddle.py --dataset lab_benchmarks/2026-11-16 --split holdout --label test_tekrar",
        "```",
        "",
        f"Kod SHA-256: `{report['code_sha256']}`",
        "",
    ]
    (dataset / "rapor.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--publish-lab", type=Path)
    args = parser.parse_args()
    report = evaluate(args.dataset)
    index_path = args.dataset / "published.json"
    published = (
        publish(args.dataset, report, args.publish_lab)
        if args.publish_lab
        else json.loads(index_path.read_text()) if index_path.exists() else {}
    )
    markdown(args.dataset, report, published)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
