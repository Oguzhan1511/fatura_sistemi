# PaddleOCR fatura deneyi — 16 Kasım 2026

14 PDF, 12 farklı fatura, 8 firma. 2 PDF aynı faturanın farklı taramasıdır.

## Ölçüm kapsamı

Numara, tarih, para birimi, kalem sayısı, miktar, birim fiyat, KDV oranı, satır tutarı ve net/KDV/brüt/ödenecek/tevkifat toplamları kontrol edildi. Ürün/satıcı metinleri, açıklama, birim ve notlar bu sayısal başarı hesabına dahil değildir. Boş veya görselden kesin doğrulanamayan referans alanları puanlanmaz. Referanslar kaynak görsellerden elle çıkarılmıştır; kullanıcı onayı değildir. Bu ölçüm bütün faturanın veya her yeni düzenin hatasız okunduğu anlamına gelmez.

## Sonuç

| Grup | PDF | Eşleşen alan | Puanlanan alanları eşleşen PDF |
|---|---:|---:|---:|
| Geliştirme | 9 | 146/147 | 8/9 |
| Ayrılan test | 5 | 67/68 | 4/5 |

Testte gerçekten yeni fatura: 3/4 eşleşti. Yeni firma örneği: 0/1 eşleşti. Dolayısıyla farklı firmalara genelleme kanıtlanmış değildir.

## Belge bazında

| Belge | Grup / firma | Alanlar | Kalan hata veya sınır | İncele |
|---|---|---:|---|---|
| F01 | Geliştirme / Sinerji | 14/15 | items.1.quantity: beklenen 1, okunan None; Numara önekindeki O/0 baskı görselinden kesin ayrıştırılamıyor; kullanıcı teyidi gerekiyor. | [Aç](http://127.0.0.1:8767/#document/493f6209687e4d79b7446dc8fc372922) |
| F02 | Geliştirme / Bulut | 12/12 | Puanlanan alanlar eşleşti; metin alanları ayrıca kontrol edilmeli. | [Aç](http://127.0.0.1:8767/#document/6b043a573aff44ccbbdebedbe30e2b98) |
| F03 | Geliştirme / Sistaş | 12/12 | Puanlanan alanlar eşleşti; metin alanları ayrıca kontrol edilmeli. | [Aç](http://127.0.0.1:8767/#document/75af5208b8ca413a86825f28e2b49549) |
| F04 | Geliştirme / Bilkur | 12/12 | Puanlanan alanlar eşleşti; metin alanları ayrıca kontrol edilmeli. | [Aç](http://127.0.0.1:8767/#document/f89cdcdb993c490a873c39e4a6099f17) |
| F05 | Geliştirme / Natro | 24/24 | Puanlanan alanlar eşleşti; metin alanları ayrıca kontrol edilmeli. | [Aç](http://127.0.0.1:8767/#document/e14018b1006b412ba4d3fb38cb432304) |
| F06 | Geliştirme / LTS | 12/12 | Puanlanan alanlar eşleşti; metin alanları ayrıca kontrol edilmeli. | [Aç](http://127.0.0.1:8767/#document/ef77784c2a9f4f4f9fbda5e54f1f67cf) |
| F07 | Geliştirme / Sinerji | 23/23 | Numara önekindeki O/0 baskı görselinden kesin ayrıştırılamıyor; kullanıcı teyidi gerekiyor. | [Aç](http://127.0.0.1:8767/#document/04af4b0cfa244dfeb017abb4afaff686) |
| F08 | Geliştirme / CPrint | 25/25 | Puanlanan alanlar eşleşti; metin alanları ayrıca kontrol edilmeli. | [Aç](http://127.0.0.1:8767/#document/4e8d6f7c5ad044dd9695393559f8b5ee) |
| F09 | Geliştirme / Bulut | 12/12 | Puanlanan alanlar eşleşti; metin alanları ayrıca kontrol edilmeli. | [Aç](http://127.0.0.1:8767/#document/adf61d422e9c41449e644c5308899162) |
| F10 | Test / CPrint | 16/16 | Puanlanan alanlar eşleşti; metin alanları ayrıca kontrol edilmeli. | [Aç](http://127.0.0.1:8767/#document/00a93d1e9fca452fa18f121f55d8e465) |
| F11 | Test / Sistaş | 12/12 | Puanlanan alanlar eşleşti; metin alanları ayrıca kontrol edilmeli. | [Aç](http://127.0.0.1:8767/#document/ff84137aaad24e64a96423fe8cfc42f5) |
| F12 | Test / CPrint | 17/17 | Puanlanan alanlar eşleşti; metin alanları ayrıca kontrol edilmeli. | [Aç](http://127.0.0.1:8767/#document/d518a0bc7de4434682563db06057ad00) |
| F13 | Test / CPrint | 12/12 | Puanlanan alanlar eşleşti; metin alanları ayrıca kontrol edilmeli. | [Aç](http://127.0.0.1:8767/#document/310a9a014f784174b95b1c843e7d6ae6) |
| F14 | Test / İleti | 10/11 | items.0.quantity: beklenen 200000, okunan 0; Numara önekindeki O/0 görselden kesin ayrıştırılamıyor; kullanıcı teyidi gerekiyor.; Özel iletişim vergisi ortak şemada ayrı alan olarak desteklenmiyor; toplam kontrolü eksik kalabilir. | [Aç](http://127.0.0.1:8767/#document/028845f0f99a47199feb3a1d579ada13) |

## Geliştirme ve tekrar üretim

Geliştirme başlangıcı: 139/147 alan. Küçük miktarlar için ek yerel okuma, para alanında açık binlik ayıraç onarımı ve doğrudan etiketli tevkifat okuması eklendi. Tutar veya miktar hesaplanıp kaynak yerine yazılmadı. Yardımcı OCR düşük güvenli olabilir; sonuçlar onay bekler.

O/0 belirsizliği bulunan F01, F07 ve F14 numaraları kullanıcı tarafından teyit edilmelidir. F01 ve F14 miktarları ayrıca kontrol edilmelidir. F14 ek vergi şeması desteği gerektirir.

Ayrım manifest.json içinde OCR öncesinde sabitlendi. Test çıktısı görüldükten sonra çıkarım kodu değiştirilmedi. freeze.json ile her deneyin kod özeti denetlenir. OCR önbelleği sadece görsel gözlemler içerir, referansları içermez. Önbellekli tekrar süreleri yeni faturanın işlem süresi değildir.

```sh
python benchmark_paddle.py --dataset lab_benchmarks/2026-11-16 --split development --label tekrar
python benchmark_paddle.py --dataset lab_benchmarks/2026-11-16 --split holdout --label test_tekrar
```

Kod SHA-256: `e2146220c0b4b31e227ae1ab9e273188a58d41c1fdbb84e4b2c450172251fa15`
