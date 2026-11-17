# Genel fatura okuma için sonraki aşama

Mevcut uygulamanın kayıt, düzenleme ve analiz katmanı ile çıkarım katmanı ayrı değerlendirilmelidir. Mevcut çıkarım Tesseract ve başlık/konum kurallarına dayanır; genel amaçlı, güvenilir bir Türkçe fatura okuyucusu olarak doğrulanmış değildir.

## Ölçüm

`evaluate_invoices.py` onaylı kayıtlardaki kullanıcı değerlerini referans alır. İlk saklanan okumalar veya `--rerun` ile güncel motor ölçülür. Kayıtlar değiştirilmez; rapor `data/evaluation` altında özel veri olarak kalır.

```sh
python evaluate_invoices.py
python evaluate_invoices.py --rerun --output data/evaluation/current.json
```

İlk yedi onaylı kayıt geliştirme sırasında görülmüş belgelerdir. Bazı referanslar hatalı OCR değeriyle onaylanmış olabilir. İnceleme bekleyen başarısız belgeler puanlanmadığı için bu kümenin skoru genel başarı oranı değildir. 20–30 farklı yerleşimli yerel belgeyi, başarısız örnekler dahil, elle doğrulanmış alan ve kalemlerle değerlendirmek gerekir. Aynı faturanın kopyaları kaynak SHA-256 ile ayırt edilir. Aynı tedarikçinin farklı kalem sayısı ve sayfa sayıları da yer almalıdır. Yeni tedarikçilerden ayrılmış, geliştirmede kullanılmayan bir küme gereklidir.

Ölçütler: fatura numarası/tarih/satıcı, tam kalem sayısı, miktar-fiyat-KDV eşleşmesi, para birimi, net/KDV/brüt/ödenecek/tevkifat değerleri, tam doğru belge oranı, süre ve bellek. Miktar ve fatura numarası hesap sonucundan türetilmez. Boş referans alanı başarı sayılmaz.

## Karşılaştırılacak yöntemler

1. Metin katmanlı PDF: doğrudan metin ve konum; mümkünse kullanıcı tarafından sağlanan UBL/XML asıl veri.
2. Türkçe metin ve tablo düzeni: PaddleOCR PP-OCRv5 Latin/Türkçe tanıma ve uygun tablo/düzen bileşenleri. Tesseract'a karşı aynı belgeler üzerinde denenmeli. Daha iyi OCR, alan eşleştirmesini tek başına çözmez.
3. Değişken düzenler: aynı ortak şemaya çıkarım yapan küçük bir yerel belge/görsel modeliyle karşılaştırma. M1/16 GB üzerinde hız, bellek, lisans ve ağırlık sürümü ölçülmeden model seçilmiş sayılmaz.
4. Decimal tutarlılık kontrolleri ve kullanıcının son onayı korunur. Tevkifat, indirim ve döviz karşılıkları ayrı alanlardır. Belirsiz değer veya model uyuşmazlığı otomatik doğru kabul edilmez.

Kaynaklar:
- https://www.paddleocr.ai/main/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html
- https://www.paddleocr.ai/main/en/version3.x/algorithm/PP-StructureV3/PP-StructureV3.html

Bu aşamada PaddleOCR veya yeni görsel model kurulup ölçülmedi. Ölçüm altyapısı eklendi; mevcut motorun yeni faturaları güvenilir okuduğu iddia edilmiyor.
