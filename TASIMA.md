# Başka bilgisayara kurulum

Bu depo mevcut fatura PDF'lerini, Excel başlangıç verilerini, ana sistem ve laboratuvar veritabanlarını içerir. **Depoyu private tutun.** GitHub'a eriştiğiniz hesap başka bilgisayarda da bu repoya erişebilmelidir.

## İndirme

Git ile klonlayın:

```sh
git clone https://github.com/Oguzhan1511/fatura_sistemi.git
cd fatura_sistemi
```

GitHub'dan ZIP indiriyorsanız bütün klasörleri birlikte çıkarın. `data`, `lab_data` ve `lab_benchmarks` özel kayıtları içerir; yalnızca Python dosyalarını almak mevcut kayıtları taşımaz.

## Ana sistemi kurma

Python **3.12** kurun. Windows'ta `Kurulum.bat`, macOS'ta `Kurulum.command` dosyasını çalıştırın. Terminalden eşdeğeri:

```sh
# Windows:
py -3.12 scripts/setup_local.py
# macOS / Linux:
python3.12 scripts/setup_local.py
```

Kurulum internet erişimi ister. Paketler `.venv-ocr` içine kurulur; başka bilgisayarın sanal ortamı kopyalanmaz. PDF'lerin okunması için ayrıca **Poppler** kurup `pdftoppm` komutunu PATH'e ekleyin. İsteğe bağlı **Tesseract**, küçük miktar hücrelerinde yardımcı okuma sağlar. macOS'ta sistem paketleri Homebrew ile `brew install poppler tesseract` komutuyla kurulabilir. Windows/Linux'ta aynı araçların işletim sistemine uygun sürümlerini kurun. `pdftoppm -v` ve `tesseract --version` komutlarıyla erişimi kontrol edin.

## Başlatma

Windows: `Baslat.bat`. macOS: `Baslat.command`. Terminal:

```sh
python start_local.py --open
```

Adres: http://127.0.0.1:8765

Ana sistem `.venv-ocr` ortamını otomatik bulur. Veriler `data` altında korunur; tekrar içe aktarma gerekmez. Kullanıcı açıklamalarına göre hizmet eşleştirme, zam analizi, fatura numarası araması ve mükerrer engelleme birlikte taşınır. Önceden üretilmiş PDF önizlemeleri de verilerle birlikte gelir.

Türkçe PaddleOCR mobil model ağırlıkları `lab_models/paddlex/official_models` içindedir. Bunlar ana okuyucunun kullandığı yerel modellerdir. Ağır OCR süreci hedef bilgisayardaki yeni Python ortamını kullanır. Bu proje macOS Apple Silicon üzerinde doğrulandı; Windows/Linux'ta uçtan uca doğrulama henüz yapılmadı.

## Laboratuvar ve isteğe bağlı Qwen

Ana sistem için Qwen gerekmez. Laboratuvar kayıtları `lab_data` içinde, deney kaynakları `lab_benchmarks` içinde korunur. Qwen'in yaklaşık 1,7 GB ağırlığı ve eski Mac sanal ortamı Git'e eklenmez; Windows/Linux, Mac'e özel MLX motorunu çalıştıramaz.

Apple Silicon Mac'te Qwen deneyi için `requirements-lab-macos.lock.txt` önceki ortamın sürüm kaydıdır. Uygun `.venv-lab` ortamına bu bağımlılıklar kurulup `python scripts/download_qwen_lab.py` çalıştırılarak sabit revizyonlu model yeniden indirilebilir. Laboratuvar arayüzünde modellerin hazır bilgisi yeni kurulumda ayrıca doğrulanmalıdır; önceki bilgisayarın hazır işareti taşınmaz. Ana sistemin PaddleOCR kurulumu bundan bağımsızdır.

## Yedek ve sonraki Git güncellemeleri

Kayıt ekledikten sonra bütün `data` ve `lab_data` klasörlerini ayrıca yedekleyin. Git'teki veri tabanları aktarım anının kopyasıdır; başka bilgisayardaki yeni kayıtları otomatik eşitlemez. Çalışan uygulamanın verilerini zorla `git reset --hard` ile sıfırlamayın. Güncelleme veya bilgisayarlar arası birleştirme öncesinde uygulamayı durdurup bu klasörlerin yedeğini alın.

Testler:

```sh
python -m unittest discover -s tests -q
```
