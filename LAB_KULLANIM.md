# Fatura Okuma Laboratuvarı

Test adresi: http://127.0.0.1:8767/#upload
ERP adresi: http://127.0.0.1:8765

## Başlatma

macOS'ta `Lab_Baslat.command` dosyasına çift tıklayın. Windows'ta gerekli Python ve OCR kurulumlarından sonra `Lab_Baslat.bat` kullanılır. Terminalden:

```sh
python3 start_local.py --lab --open
```

## Fatura deneme

1. Üstteki **Etkin okuyucu** listesinden **PaddleOCR** veya **Qwen3-VL** seçin, ardından PDF veya fotoğraf yükleyin.
2. Belge önizlemesiyle okunan alanları karşılaştırın.
3. Hataları düzeltin; **Taslak kaydet** ile düzeltmeleri saklayın.
4. Tüm alanlar doğrulandığında **Referans olarak doğrula** seçeneğiyle karşılaştırma için referans kayıt oluşturabilirsiniz.
5. Üstteki test panelinden **Başarılı / Kısmen doğru / Hatalı** seçin, sorunlu alanları yazın ve **Test sonucunu kaydet** düğmesine basın. Bu değerlendirme alan düzeltmelerinden ayrı saklanır.
6. **Test Belgeleri** sayfasından önceki denemeleri tekrar açabilirsiniz. İlk okunan değerler ve yaptığınız düzeltmeler ayrı kalır.
7. Belge içindeki karşılaştırma bölümünden diğer motoru seçip **Bu belgeyi seçili motorla dene** düğmesine basın. Aynı kaynak belge için yeni test kaydı açılır; önceki sonuç ve düzeltmeler korunur.

## İzolasyon ve mevcut okuyucu

Tüm yüklemeler, SQLite kayıtları ve test notları `lab_data` altındadır. ERP'nin `data` klasörü kullanılmaz ve kayıt aktarımı yapılmaz. Laboratuvarın ERP veri klasörüyle başlatılması engellenir. Ağır modeller `.venv-lab` ortamında ayrı süreçlerde, bellek kullanımını sınırlamak için sırayla çalışır. İş bitince model süreci kapanır.

Kurulan motorlar:

- **PaddleOCR 3.3.2 / PaddlePaddle 3.2.0:** PP-OCRv5 mobil metin algılama ve Türkçeyi destekleyen Latin metin tanıma. OCR çıktısı mevcut başlık ve alan eşleştirme koduyla yapılandırılır; bu eşleştirme hâlâ hata yapabilir.
- **Qwen3-VL-2B-Instruct, 4 bit / MLX:** görselden doğrudan JSON üretir. Bu kurulum Apple Silicon Mac içindir; aynı MLX motoru Windows/Linux'ta çalışmaz. Küçük modelin sayıları, harfleri ve alanları karıştırabildiği gözlendi.
- **Mevcut prototip:** eski yöntemi karşılaştırmak için kullanılabilir.

İki farklı gerçek fatura üzerinde her iki yeni motorla çıkarım tamamlandı. Dört kalemli örnekte ikisi de dört satır buldu; miktarlar, fatura numarası ve bazı toplamlar hatalı veya eksik kaldı. Bu çalışma genel fatura doğruluğunun sağlandığı anlamına gelmez. Ölçümler `lab_models/smoke_results.json` içindedir. İlk yükleme dahil ölçülen süreler yaklaşık 26–86 saniyedir; belge ve sayfa sayısıyla değişir.

Model ve paketler kurulumda internetten indirildi; fatura çıkarımı bilgisayarda yapılır. Ağırlıklar `lab_models` altında tutulur. Sayfa başına ham Qwen çıktısı ve işlem günlükleri ilgili test belgesinin dosya klasöründe bulunur. Hassas fatura verisi içerebilirler.

Bu Mac'te kurulan bağımlılık sürümleri `requirements-lab-macos.lock.txt` dosyasındadır; Windows/Linux kurulum dosyası değildir. Yeni motorlar önce bu laboratuvarda karşılaştırılacak; ERP'ye geçiş ayrı bir değişiklik olacaktır.

Laboratuvar verilerini yedeklemek için uygulamayı durdurup `lab_data` klasörünü kopyalayın. Silme işlemi ERP'deki gibi kaydı listeden çıkarır; fiziksel dosyalar geçmiş için kalır.

## Ölçüm

Kullanıcı doğrulaması tamamlanan laboratuvar referanslarını değerlendirme aracına verebilirsiniz:

```sh
python evaluate_invoices.py --data-dir lab_data --output lab_data/evaluation/baseline.json
```

Yalnızca başarıyla onaylanmış kayıtlarla alınan skor tüm belgelerin başarı oranı değildir. Kısmen doğru ve hatalı sonuçlar test notlarıyla birlikte değerlendirilmelidir.

## 16 Kasım 2026 toplu deneyi

14 PDF proje içindeki özel `lab_benchmarks/2026-11-16` klasöründe korundu. Bunlar 12 farklı fatura ve 8 firmayı kapsıyor; iki dosya başka bir faturanın yeniden taraması. Ayrım OCR öncesinde 9 geliştirme + 5 test olarak sabitlendi. Test çıktıları görüldükten sonra çıkarım kodu değiştirilmedi.

Görsel referanslarla puanlanan kritik alanlar geliştirmede 8/9, ayrılan testte 4/5 PDF'de eşleşti. Yalnızca gerçekten yeni test faturalarında sonuç 3/4'tür. Tek yeni firma örneğinde miktar hatası vardır; yeni firmalara genelleme kanıtlanmış değildir. Sayısal ölçüm metin adlarını/notları ve kesin doğrulanamayan numara öneklerini kapsamaz. Ayrıntılar ve belge bağlantıları özel deney klasöründeki `rapor.md` dosyasındadır.

Küçük miktar hücreleri ayrıca iki ölçekte metin modeliyle, gerekirse kurulu Tesseract'ın İngilizce rakam okumasıyla kontrol edilir. Tesseract isteğe bağlıdır; kurulu değilse bu yardımcı yol kullanılamaz. Ek okumalar inceleme uyarısı taşır.

14 çıktı laboratuvara **Deney F01…F14** adlarıyla, onay bekleyen kayıt olarak aktarıldı. Referans değerler okunan alanların yerine yazılmadı. Karşılaştırma verisi ve kaynak faturalar hassas veri içerir; bu klasör sürüm kontrolüne eklenmez.

Arayüzde tam tutarlar `140.000`, kuruşlu tutarlar `1.778,10` biçimindedir. Birim fiyatın `7.481,5008` gibi hassas küsuratı korunur. Görünümdeki binlik ayıracı sunucuya kaydedilen sayıyı değiştirmez.
