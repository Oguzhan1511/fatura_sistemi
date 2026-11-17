# Miktar hücresi düzeltmesi — 16 Kasım 2026

F14 miktarı tam sayfa OCR'sinde 200.000 olarak görülmesine rağmen hücre soldan dar kırpılmış, 00.000 → 0 olmuştu. Tek sayısal adayın tam OCR kutusu miktar hücresine dahil edildi; ürün/ad sütununun bu alana taşması engellendi. Miktar tutarlardan hesaplanmadı.

[Yeni laboratuvar sonucu](http://127.0.0.1:8767/#document/dab6c3a4d05346f0ac257857f55c052e)

14 belgede regresyon çalıştırıldı. F14 miktarı 200000 oldu; önceki doğru puanlanan alanlarda kayıp görülmedi. F01'deki bir miktar hâlâ boş. Üç numara önekinin referans belirsizliği ve F14 ek vergi şeması eksikliği devam ediyor.

Bu düzeltme önceki test sonucu görüldükten sonra yapıldı; dolayısıyla yeni sonuç bağımsız başarı oranı değildir. İlk deney raporu ve freeze.json değiştirilmedi. Güncel tekrar için benchmark_paddle.py --split regression kullanılabilir.
