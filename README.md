# Fatura Sistemi — başka bilgisayara aktarım

Yeni bilgisayarda kurulum için **[TASIMA.md](TASIMA.md)** dosyasını izleyin. Python 3.12 ile `Kurulum.bat` (Windows) veya `Kurulum.command` (macOS) yeni `.venv-ocr` ortamını kurar. Poppler ayrıca gereklidir.

Bu private depo uygulama kodlarını, mevcut `data` / `lab_data` kayıtlarını, Excel başlangıç verilerini, deney belgelerini ve ana sistemin Türkçe PaddleOCR mobil ağırlıklarını içerir. Fatura verileri bulunduğu için **depoyu public yapmayın**. Sanal ortamlar, paket önbellekleri ve isteğe bağlı büyük Qwen ağırlıkları yeniden kurulur; indirme aracı projededir.

Güncel özellikler: PDF okuma ve kontrol, miktar/KDV/not alanları, hizmet bazında zam analizi ve fiyat grafikleri, numarayla arama ve mükerrer fatura engelleme. Ana sistem `8765`, laboratuvar `8767` portunda çalışır.

---

# Web uygulaması hazır

Yerel ERP arayüzünü açmak için macOS'ta **Baslat.command** dosyasına çift tıklayın veya `python3 start_local.py --open` çalıştırın. Adres: `http://127.0.0.1:8765`.

PDF yükleme, belge önizlemesi, düzenlenebilir alanlar, onay sonrası SQLite kayıt, fatura listesi, ilk filtreler ve grafiklerle analiz hazır. Kamera/fotoğraf yükleme seçenekleri kaldırıldı; önceden yüklenen görseller korunur. Kurulum, kullanım ve sınırlar: [KULLANIM.md](KULLANIM.md).

**16 Kasım 2026:** Ana sistemde varsayılan okuyucu PaddleOCR'dır. Laboratuvarda denenen miktar, başlık ve satır eşleştirme düzeltmeleri aynı model işçisinde kullanılır. Bu bilgisayarda `.venv-lab` ortamı otomatik bulunur; ayrı kurulum için `requirements-paddle.txt` kullanılabilir. Model her işte ayrı süreçte çalışır ve işler sırayla yürür. Mevcut kayıtlar korunur; kullanıcı incelemesi ve onayı devam eder. Laboratuvar `8767` adresinde bağımsız kalır.

Aşağıdaki bölümler önceki çıkarım prototipinin tarihsel geliştirme notlarıdır. Güncel ana sistem motoru yukarıdaki PaddleOCR kurulumudur.

---

# Güncel kullanım: taşınabilir OCR ve miktar okuma

Taranmış PDF yolu artık varsayılan olarak **Tesseract** kullanır. `Vision` yalnızca `--ocr-engine vision` ile seçilen, macOS'a özel bir alternatiftir. Metin katmanlı PDF yolu motor gerektirmez. Windows/Linux üzerinde henüz uçtan uca test yapılmadı; sistem bağımlılıklarının her platformda kurulması gerekir. Python tarafındaki `resource` bağımlılığı da isteğe bağlı hale getirildi; Windows'ta ölçülemeyen tepe bellek `null` olur.

## Kurulum

Python sanal ortamı oluşturun ve `python -m pip install -r requirements.txt` çalıştırın. Bu geliştirmede yerel Python 3.12 ortamı kullanıldı. Tesseract ve Poppler ayrıca kurulmalıdır:

- macOS: `brew install tesseract poppler`.
- Debian/Ubuntu kullanılıyorsa: `sudo apt install tesseract-ocr poppler-utils`.
- Windows: [Tesseract kurulum sayfasındaki](https://tesseract-ocr.github.io/tessdoc/Installation.html) Windows dağıtımını kurun; Tesseract ve Poppler yürütülebilir dosyalarını PATH'e ekleyin. PATH kullanılamıyorsa `--tesseract` ve `--renderer` ile tam yolları verin. Windows için henüz çalıştırma testi yapılmadı.

Türkçe ve İngilizce `tessdata_fast` 4.1.0 ağırlıkları `models/tessdata` içinde indirildi. Sürümleri, kaynak adresleri ve SHA-256 değerleri `manifest.json`, lisans metni `LICENSE` içinde bulunur. Yerel ağırlıklar bulunursa otomatik seçilir; farklı bir klasör `--tessdata` ile verilebilir. Çalıştırma sırasında indirme veya bulut API çağrısı yapılmaz. Tesseract 5.5.4 bu Mac'e kuruldu ve aşağıdaki komutla test edildi:

```sh
python scan_invoice.py '/Users/oguzhanozdemir/Desktop/fatura_örnek.pdf' \
  --profile profiles/sinerji_scan.json --ocr-engine tesseract \
  --tessdata models/tessdata -o output/fatura_ornek_tesseract.json
```

## Miktar doğrulaması ve bu belgedeki sonuç

Miktar hücresi kaynak görüntüden kırpılır, boş kenarlar azaltılır, büyütülür ve çerçeve eklenir. Aynı Tesseract motorunun tek sözcük ve ham satır segmentasyonları (PSM 8/13) çalıştırılır. İki geçerli metin uyuşmadığında miktar kabul edilmez. Bu iki bağımsız model değildir; aynı motorun iki ayarının uyuşması doğruluk garantisi sağlamaz. Ham denemeler `.ocr.json` dosyasında, alan metni ve kaynak bölgesi sonuç JSON'unda korunur. Ürün satırı toplamı/fiyat oranından miktar türetilmez.

Sonuç: iki miktar da **1**, oranlar **%0 ve %20** olarak okundu. Her iki miktar × birim fiyat kontrolü geçti. Net **8.000,00 TL**, KDV **320,00 TL**, brüt/ödenecek **8.320,00 TL**. Tesseract Türkçe unvan ve hizmet adlarını bu örnekte daha iyi okudu; fatura numarasının ilk karakterini `$` okuduğundan numara tahminle düzeltilmedi, `null` bırakıldı ve ham metin korundu. Vergi esası açık ifade ile doğrulanamadığından hala `unknown`. Sayfa düzenine özel bölge profili ve satır sayısını kontrol etme ihtiyacı devam ediyor; çıktı `needs_review: true`.

Testler: `python -m unittest discover -s tests -v`. Boş miktar, tek/çok basamaklı ve kesirli miktar, iki okumanın anlaşmazlığı, alternatif satır çapası ve macOS dışı Vision reddi kapsanır. Yeni testlerin bir bölümü kurulu gerçek Tesseract motorunu kullanır; motor/ağırlık yoksa ilgili entegrasyon testi atlanır.

PaddleOCR araştırma adayı olarak duruyor; bu adımda dar miktar hücresi sorununu küçük, CPU üzerinde çalışan Tesseract ile çözdük. Bu sonuç tüm fatura düzenlerine genellenemez.

---

Aşağıdaki bölümler önceki prototip aşamalarını ve sınırlarını kaydeder; güncel motor seçimi ve komutlar yukarıdadır.

# Yerel fatura çıkarımı — ilk prototip

macOS 15.3.1, Apple M1 (8 CPU/7 GPU çekirdeği), 16 GB RAM üzerinde geliştirildi. Bulut/API çağrısı veya model indirmesi yapmaz. Çalışma klasörü başlangıçta boştu. Python 3.14 sistemde mevcut; paket indirmesi ağ kısıtı nedeniyle tamamlanamadı. Testler Codex'in yerel paketli Python ortamında çalıştırıldı.

## Kurulum ve kullanım

Normal internet erişimi olan terminalde proje klasöründe:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python examples/generate.py
python invoice.py examples/multi_page.pdf -o output/sonuc.json
python -m unittest discover -s tests -v
```

Mevcut bilgisayarda paket kurulumu gerektirmeden doğrulanan çalıştırma:

```sh
/Users/oguzhanozdemir/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 invoice.py examples/multi_page.pdf -o output/sonuc.json
```

Son komut Codex kurulumuna özgüdür; taşınabilir kurulum için sanal ortamı kullanın. Örnek üreticinin font yolu macOS Arial fontuna bağlıdır. Çıkarımın kendisinde bu font bağımlılığı yoktur.

## İşleyiş ve destek sınırı

`invoice.py`: sayfa bazında pdfplumber ile sözcükleri ve koordinatlarını okur, satırları oluşturur, tanımlı etiketleri ve `|` ayrılmış tabloyu ayrıştırır. Bu bir genel amaçlı Türkçe fatura okuyucusu değildir: farklı tedarikçi düzenleri için yeni ayrıştırıcı gerekir. Sentetik faturanın `net`/`gross` sütunu vergi esasını açıkça belirtir; gerçek belgelerde bunu belirleyen şablon geliştirilmelidir. Satır sayısında sabit sınır yoktur.

Tamamen metinsiz sayfalar `ocr_required` ile işaretlenir. Karışık dosyada metinli sayfalar işlenir, metinsiz sayfalar kontrol nedenine eklenir. **Aynı sayfadaki metin + görsel tablo ve bozuk/eksik metin katmanı güvenilir biçimde tespit edilmiyor.** OCR, fotoğraf düzeltme ve görsel model henüz uygulanmadı. Kaynak dosya tek fatura kabul edilir; bir dosyadaki farklı faturalar otomatik bölünmez.

Etiketler: Satıcı, VKN, Adres, Fatura No, Fatura Tarihi, Para Birimi, KDV Hariç Toplam, KDV Toplam, KDV Dahil Toplam, İndirim Toplam, Tevkifat, Ödenecek Tutar.

Tablo başlığı: `Ürün | Açıklama | Miktar | Birim | Birim Fiyat | KDV | Satır Toplam | Esas`.

## Ortak veri sözleşmesi

`schema.json` JSON Schema sözleşmesidir. Tek fatura nesnesinin `items` dizisinde her kalem ayrı nesnedir. Tüm parasal değerler ve miktarlar ondalık metindir; hesaplarda Decimal kullanılır. Fatura numarası ve VKN metindir. Eksik alan `null` kalır; para birimi varsayılmaz. Tarih ISO biçimine çevrilir. Girdi sayıları Türkçe biçimde beklenir; yabancı sayı biçimi tahmin edilmez.

`seller`: name, tax_id, address. `totals`: net, vat, gross, discount, withholding, payable. Kalemlerde name, description, quantity, unit, unit_price, vat_rate, line_total, discount, price_basis ve total_basis bulunur. Oran `20` gibi yüzde değeridir. Esas `net`, `gross` veya `unknown` olur.

`evidence` ve kalem `evidence` alanları sayfa, ham metin ve `[x0, top, x1, bottom]` konumlarını içerir. Birim PDF noktasıdır; başlangıç sol üsttedir. `pages` ham satırları da korur. `checks` okunan ve hesaplanan tutarları ayırır. `issues` neden kodlarını içerir; `needs_review` bunlardan türetilir. Otomatik kontrolün temiz olması gerçek belge doğruluğunu kanıtlamaz.

Miktar × fiyat, satır ve genel toplam kontrolleri 0,01 toleransla yapılır. Karma KDV oranları desteklenir. Genel indirim/tevkifat varsa değer korunur ve matrah dağılımı için kontrol istenir; indirimli toplamlar otomatik onaylanmaz. Tevkifat açıkça belirtilirse brüt − tevkifat ile ödenecek tutar karşılaştırılır. Satır indirimi ayrıştırması henüz yoktur; şemada alan ayrılmıştır. Okunan tutarlar hiçbir zaman hesap sonucuyla değiştirilmez.

## Doğrulanan sonuçlar

Altı unittest geçti: Türkçe sayı ayrıştırma, iki sayfadan üç kalem çıkarma, tekrar eden başlık, farklı KDV, boş açıklama, belirsiz vergi esası, eksik/metinsiz sayfa, ham tutarın korunması ve hatalı toplam işaretleme. Karışık sayfa testi ara çıktı düzeyindedir; gerçek taranmış PDF ile OCR testi değildir.

Sentetik doğru örnek: net 3.269,12; KDV 623,82; brüt 3.892,94; üç kalem, yedi başarılı hesap kontrolü. Hatalı örnekte brüt 3.900,00 aynen tutulur ve kontrol gerektirir. İlk ayrı CLI ölçümleri yaklaşık 0,078 ve 0,059 saniye; süreç tepe belleği yaklaşık 39 MB. Bellek `ru_maxrss` ile macOS'ta bayt cinsindendir ve yalnızca bu işin ek bellek maliyeti değildir.

Bu iki kontrollü örnekte kontrol gerektiren belge oranı 1/2'dir; üretim başarımı olarak yorumlanamaz. Gerçek satıcı/tarih/numara doğruluğu, kalem kapsama oranı ve OCR başarısı henüz ölçülmedi. Sonraki adım birkaç yerel PDF ve elle doğrulanmış beklenen JSON ile tedarikçi şablonlarını değerlendirmektir.

## Model adayları — 14 Kasım 2026 kaynak incelemesi

Hiçbir model kurulmadı veya bu cihazda denenmedi; ağırlık sürümleri sabitlenmedi. Aşağıdakiler kaynak beyanıdır, yerel uyumluluk garantisi değildir.

- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR): Apache-2.0 proje lisansı. OCR için ilk deney adayı; seçilecek paket/model sürümünün macOS ARM/Python uyumu, Türkçe tanıma ağırlıkları ve lisansı ayrıca doğrulanmalı. PP-Structure ayrı değerlendirilir.
- [Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct): kartta Apache-2.0 ve Transformers kullanımı mevcut. 7 milyar parametrenin yalnızca 16 bit ağırlıkları kabaca 14 GB gerektirir; görsel girdiler ve çalışma belleği buna eklenir. Bu hesap 16 GB paylaşımlı bellekte yeterlilik iddiasına izin vermiyor. Daha küçük veya nicemlenmiş sürüm ancak backend, ağırlık lisansı ve yerel ölçümle seçilmeli.
- [dmr-invoice-extractor](https://huggingface.co/rhovhannisyan/dmr-invoice-extractor): kartta CC-BY-NC-SA-4.0; ticari olmayan kullanım koşulu dikkate alınmalı. Ürün satırları/Türkçe kapsamı doğrulanmadı; tam çözüm seçilmedi.
- [invoice2data](https://github.com/invoice-x/invoice2data): MIT lisanslı şablon tabanlı yaklaşım. İlk prototip benzer biçimde açık kurallarla çalışır; bu paket bağımlılık olarak eklenmedi.
- [TurkceOCR](https://github.com/bilersan/TurkceOCR): depo Apache-2.0, SVTRv2 ve Qwen LoRA bileşenleri belirtiyor. Ağırlıklar, model bağımlılıkları ve yerel çalışma henüz denetlenmedi. Özellikle tutar düzeltme davranışı bizim ham değeri koruma kuralımızla ayrıca değerlendirilmelidir.
- [Future OCR](https://github.com/SafiCeylan/Future_ocr-otomatik-a-destekli-fi-okuma-sistemi): yöntem referansı; README eğitilmiş Donut ağırlıklarının Git dışında olduğunu söylüyor. Tam lisans/ağırlık denetimi yapılmadı; bağımlılık seçilmedi.

## İkinci aşama: konum tabanlı tablolar

Yeni `layout.py`, `|` ayracı bulunmayan tablolarda sözcüklerin PDF koordinatlarını kullanır. Sütun aralıkları ve başlık ifadeleri tedarikçi şablonunda tanımlanır. Örnek yapı `examples/layout_template.json` dosyasındadır; gerçek faturaya göre ayarlanmadan kullanılması doğruluk garantisi vermez.

```sh
python invoice.py faturam.pdf --template examples/layout_template.json -o output/faturam.json
```

`columns` içindeki her aralık `[sol, sağ)` biçiminde PDF noktasıdır. Başlığın aynı metin satırında `header_contains` ifadelerinin tümünü içermesi gerekir. Her sayfada tablo başlığı yeniden aranır. `stop_prefixes` tablo bitiş etiketleridir. Sayısal alanların beklenen biçimi Türkçe olarak kalır; miktar ve birim ayrı sütunlarda olmalıdır. Fatura üst bilgileri için önceki etiket kuralları halen geçerlidir.

`net_marker` ve `gross_marker`, **belgede gerçekten yer alan** açık vergi esası ifadeleridir; şablonda varsayılan esas tanımlanmaz. İfade ilgili sayfada yoksa veya iki ifade de varsa esas belirsiz kalır. Ham sayfalar sonuçta korunur; kalemlerin kaynak konumu aynı kalır. Sözcük koordinatları da `pages[].lines[].words` içinde bulunur.

Sütunu aşan sözcük `layout_overflow` üretir. Birden fazla satıra taşan açıklama otomatik birleştirilmez; eksik sayısal alanlı satır kontrol ister. Birleşik hücreler, çok satırlı başlıklar, sağa hizalı miktar+birim tek hücresi ve başlıksız devam sayfaları için ek geliştirme gerekir. Dolayısıyla bu aşama gerçek faturalar için şablon altyapısını sağlar; henüz genel düzen algılama sağlamaz.

Güncel test sayısı 10: önceki altı teste sütun eşleştirme/ham veriyi koruma, açık vergi esası yokluğu, sütun taşması ve açıklama devam satırı senaryoları eklendi. Yeni testler koordinatlı ara çıktı üzerinde çalışır; gerçek tedarikçi PDF'siyle uçtan uca doğrulama henüz yapılmadı.

## Taranmış gerçek belge denemesi: macOS Vision

`scan_invoice.py` tek sayfalı, metinsiz PDF'yi Poppler ile 2200 piksel yüksekliğe render eder. `scripts/vision_ocr.swift` Apple Vision üzerinden önce tam sayfayı, sonra alanları ayrı bölgeler olarak yerel okur. Swift/Xcode Command Line Tools ve Poppler gereklidir. Sistem hizmetlerine erişim kısıtlanan ortamda Vision çalışmayabilir; normal macOS terminali kullanılabilir. Bulut servisi veya ücretli API yoktur.

```sh
python scan_invoice.py '/Users/oguzhanozdemir/Desktop/fatura_örnek.pdf' \
  --profile profiles/sinerji_scan.json -o output/fatura_ornek.json
```

Poppler PATH'te değilse `--renderer /tam/yol/pdftoppm` ekleyin. Profildeki koordinatlar piksel değil, sol üst başlangıçlı 0–1 oranlarıdır. Profil yalnızca örnekteki sayfa düzeni için ayarlanmıştır; farklı kaymış/eğik taramalarda otomatik hizalama yoktur. İkinci geçişte satırların sınırları OCR ile bulunan sıra numaralarından türetilir; kalem sayısı sabitlenmez. Tek sayfalı profil, ilk prototipin çok sayfalı metinli PDF desteğinin yerini almaz.

Bu cihazın Vision OCR motoru `tr-TR` bildirmediği için `en-US` kullanıldı. Desteklenen diller çalışma anında sorgulanır ([Apple dokümanı](https://developer.apple.com/documentation/vision/vnrecognizetextrequest/supportedrecognitionlanguages())). Genel Türkçe OCR için PaddleOCR karşılaştırması halen yapılmalıdır.

Kullanıcının sağladığı taranmış PDF'de iki hizmet satırı bulundu. Görsel inceleme ile doğrulanan net 8.000,00 TL, KDV bileşenlerinin toplamı 320,00 TL, brüt/ödenecek 8.320,00 TL olarak çıkarıldı. İkinci hizmetin çok satırlı adı ve ilk satır açıklaması ayrı hücrelerde tutuldu. **İki miktar hücresindeki 1 OCR ile okunamadı; JSON'da null bırakıldı.** Türkçe harfler ve fatura numarasının O/0 ayrımı elle kontrol gerektirir. Otomatik miktar tamamlama yapılmadı.

Bazı sayılarda virgül nokta okunuyor; yalnızca tanımlı ondalık desenindeki dönüşüm uygulanır ve her dönüşüm `ocr_numeric_separator` ile işaretlenir. Ham metin `evidence` içinde korunur. Vergi esası açık bir ifadeden okunamadığı için `unknown` tutulur. Dolayısıyla çıktı otomatik onaylı değildir. KDV toplamı iki ayrı okunan KDV tutarının toplamıdır; iki kanıt bölgesi de saklanır. Süre ve süreç belleği çıktıdaki `metrics` alanındadır; bu belgedeki ölçüm genel performans iddiası değildir.

`output/fatura_ornek.ocr.json` tam sayfa ve hücre OCR ham sonuçlarını içerir. Yeniden çalıştırma bu dosyayı ve sonuç JSON'unu günceller. Bu dosyalarda özel belge verileri bulunabilir. Güncel testler: `python -m unittest discover -s tests -v` (13 test).
