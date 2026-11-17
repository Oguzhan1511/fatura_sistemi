# Yerel Fatura Yönetimi

## Açma

macOS'ta `Baslat.command` dosyasına çift tıklayın. Uygulama tarayıcıda `http://127.0.0.1:8765` adresinde açılır. Terminal penceresi açık kalmalıdır; kapatmak için terminalde Control+C kullanın.

Terminalden başlatma:

```sh
python3 start_local.py --open
```

Ana sistemin varsayılan okuyucusu PaddleOCR'dır. Bu bilgisayarda hazır `.venv-lab` ortamı ve yerel ağırlıklar otomatik kullanılır. Başka bilgisayarda uyumlu Python ortamını ayrı kurun:

```sh
python -m venv .venv-ocr
# macOS / Linux:
source .venv-ocr/bin/activate
# Windows için yukarıdaki satır yerine: .venv-ocr\Scripts\activate
python -m pip install -r requirements-paddle.txt
python start_local.py --open
```

Windows'ta kurulum sonrasında `Baslat.bat` kullanılabilir. PDF önizlemesi için Poppler gerekir. Tesseract, küçük miktar hücreleri için isteğe bağlı yardımcı okuyucudur. Qwen/MLX ana sistem için gerekmez. Uygulama macOS'ta doğrulandı; Windows/Linux'ta uçtan uca test edilmedi. İlk model kurulumu internet gerektirebilir; bu bilgisayardaki ağırlıklar hazırdır. Faturalar bulut API'sine gönderilmez.

8765 numaralı port başka bir uygulamada kullanılıyorsa:

```sh
python3 start_local.py --port 8767 --open
```

## Kullanım akışı

### İnceleme ve kayıt

1. **Fatura Yükle** sayfasından PDF seçin ya da sürükleyip bırakın. Sınır 25 MB; PDF için en fazla 30 sayfa.
2. Belgenin önizlemesi yanında okunan alanlar açılır. Satıcı, fatura bilgileri, ürün/hizmet adı, açıklama, miktar, birim, fiyat, KDV ve toplamları değiştirebilirsiniz. Yeni kalem ekleyebilir veya yanlış satırı kaldırabilirsiniz.
3. Miktar dahil zorunlu alanları tamamlayın. KDV dahil/hariç esasını belgeden kontrol edin. Tutarlar hesapla sessizce değiştirilmez.
4. İsterseniz **Taslak kaydet** ile sonra devam edin. Fatura analize ancak **Onayla ve kaydet** işleminden sonra dahil olur. Uyarılar varsa incelendiğini işaretlemek gerekir; zorunlu alan eksikliği yine de onayı engeller.
5. **Faturalar** sayfası Excel kaynaklı **Zam Analizi** tablosunu açar. PDF kayıtlarına **Yüklenen faturalar** düğmesinden ulaşıp yeniden düzenleyebilirsiniz. Kayıt listesinde arama, durum, para birimi ve tarih aralığı filtreleri korunur.
6. **Analizler** sayfasında dönem ve para birimi seçin. Aylık tutar grafiği, net/KDV dağılımı, öne çıkan satıcılar ve özet yalnızca onaylı kayıtlardan hesaplanır. Farklı para birimleri toplanmaz.

Arayüz 390, 768 ve 1440 piksel genişlikleri hedeflenerek tasarlandı. 390 ve 1440 genişliklerinde Chrome tarayıcı kontrolleri yapıldı; gerçek iPhone/iPad testi yapılmadı. Mobil uyum aynı bilgisayarda dar tarayıcı penceresiyle kullanılabilir. Uygulama yalnızca 127.0.0.1 dinlediği için başka bir telefondan ağ üzerinden bağlanmaz.

## Veriler ve yedek

### Excel kaynaklı Zam Analizi

Faturalar sayfasındaki tablo yalnızca kullanıcının verdiği `2024-2026 Detay.xls` dosyasının **Zam Analizi** sayfasındaki 20 hizmet satırını içerir. 2024/2025/2026 tutarları, ilgili zam sütunları, toplam artış, fatura adedi, ürün adet fiyatı, hizmet türü, tek adet tarihi ve notlar kaynak değerleriyle aktarılmıştır. Zam oranları yeniden hesaplanmaz; boş değerler sıfır yerine “—” gösterilir. PDF kayıtları bu tabloya katılmaz.

Kaynakta bazı zam oranları yıl tutarlarıyla örtüşmeyebilir. Kullanıcının istediği gibi Excel değerleri korunur; kaynakta bir düzeltme yapılmamıştır. Açıklama/not araması ve hizmet türü filtresi bulunur. Tablo telefon ekranında yatay kaydırılır.

Excel başlangıç aktarımı `data/reference/increase-analysis.json` dosyasında, kaynak kopyası aynı klasörde saklanır. Kaynak Excel'in özeti aktarımda kayıtlıdır. **Yüklenen faturalar** bölümü onay ve silme işlemlerini ayrı tutar; **Zam analizine dön** ile Excel görünümüne dönülür.

- `data/invoices.sqlite3`: belgeler, ilk okuma, düzenlenen kayıt ve onay geçmişi.
- `data/files`: orijinal belgeler ve sayfa önizlemeleri.

Yedek almak için uygulamayı durdurup **data klasörünün tamamını** kopyalayın. Yalnızca veritabanını kopyalamak belge dosyalarını taşımaz. Test kayıtları ayrı geçici veritabanında tutuldu; esas çalışma alanına örnek faturalar eklenmedi.

Tarayıcıyı kapatmak kayıtları silmez. Uygulama yerel ve tek çalışma alanı içindir; çok kullanıcılı hesap/rol yönetimi yoktur. Başlıktaki “Mali İşler” çalışma alanı etiketidir.

## Güncel okuma yöntemi ve sınırlar

Yeni PDF faturalar, laboratuvarda denenen aynı PaddleOCR ve başlık/satır eşleştirme koduyla okunur. PDF sayfaları görsele dönüştürülür. Ağır model ayrı süreçte çalışır; işler sırayla yürütülür ve iş bitince model belleği bırakılır. Miktarlar tutarlardan hesaplanarak doldurulmaz. Okuma başarısızsa eski motora sessizce geçilmez; belge elle incelemeye açılır.

Mevcut kayıtlar topluca yeniden okunmaz veya onaylanmaz. İstenen eski belge, inceleme ekranındaki yeniden okuma işlemiyle PaddleOCR'a gönderilebilir; ilk okuma geçmişi korunur. Laboratuvar `8767` ve `lab_data` ile ayrı kalır.

Farklı düzenlerde alanlar eksik veya yanlış kalabilir; örneğin bazı ince rakamlar, numara önekleri ve ayrı ek vergi alanları kontrol gerektirir. Kullanıcı incelemesi ve onayı zorunludur. Telefon fotoğrafının EXIF yönü uygulanır; kaynak dosya değişmez.

Para hesapları ve analiz özetleri Python Decimal kullanır. Grafikteki çubuk yüksekliği yalnızca görsel oran için sayıya çevrilir. Belge verileri bir bulut API'sine gönderilmez.

## Doğrulama

```sh
python -m unittest discover -s tests -v
```

Testler çıkarım, miktar, Decimal analiz, onay gereklilikleri, ilk verinin korunması, SQLite kalıcılığı, revizyon çakışması ve ana sistemin PaddleOCR seçimini kapsar. Ana sistemin geçici kopyasında gerçek PDF/fotoğraf yükleme, 200.000 miktarı, dört hizmet kalemi, onay koruması ve mobil taşma ayrıca kontrol edilir.

Ana sistemde her belgenin klasöründe `paddle-result.json` ve `paddle-run.log` bulunur; hassas belge verisi içerebilir. Günlük dosyaları kullanıcı onayı yerine geçmez. Gerekli ortam bulunamazsa `requirements-paddle.txt` kurulumunu kontrol edin. Ortam yolu isteğe bağlı `FATURA_OCR_PYTHON` değişkeniyle belirtilebilir.

## Son inceleme iyileştirmeleri

Satıcı formunda yalnızca firma adı gösterilir. Toplamlar bölümünde kalemlerdeki farklı KDV oranları (örneğin %0 ve %20) ayrı gösterilir ve kalem oranı değişince güncellenir. Varsa Fatura Notu/Notlar başlığı altındaki metin kaynak konumlarıyla çıkarılır; not alanı elle değiştirilebilir ve onaylanan kayıtta saklanır. Başlık bulunmazsa not tahminle doldurulmaz.

Fatura numarası ilk geçişte okunamazsa yalnızca bu hücrede ek okuma ayarları denenir. Alternatif sonuç aday olarak gösterilir; I/1 ve O/0 gibi benzer karakterler kullanıcı kontrolü gerektirir. İlk ham okuma korunur; yazılımla otomatik karakter değiştirme yapılmaz.

Eski inceleme kayıtları kendiliğinden değiştirilmez. Kaydı açıp üstteki **Belgeyi yeniden oku** düğmesine basarak yeni yöntemi çalıştırabilirsiniz. Onaylanan kayıtlar otomatik yeniden analiz edilmez. Yeniden okumalar ayrı geçmişe eklenir, ilk okuma korunur.

## Farklı yerleşimler için başlık tabanlı okuma

Özel tedarikçi profili bulunmadığında artık fatura numarası/tarihi ve toplam etiketleriyle tablo sütunları sayfanın gerçek konumlarından aranır. Miktar, birim fiyat, KDV oranı ve mal/hizmet tutarı başlıkları tanınırsa kalem hücreleri ayrı okunur. Metinli PDF'lerde aynı eşleştirme doğrudan sözcük konumlarıyla, OCR çalıştırılmadan yapılır. Sabit ürün sayısı veya yeni faturadaki firma adını arayan bir kural kullanılmaz.

Etiketsiz dipnotlar, toplamların altındaki ayrı açıklama bloğunda bulunursa not adayı olarak gösterilir ve kontrol uyarısı eklenir. Tüm düzenler desteklenmez: başlıkların okunamadığı, çok farklı adlandırıldığı veya devam sayfasında bulunmadığı tablolarda eksik alanlar kalabilir. KDV dahil/hariç esası belgeden açıkça okunamadığında yine belirsiz bırakılır. Yeni yöntemde alanların doğru hücrelerden geldiğini kullanıcı doğrular.

Tablo ilk okumada bulunamazsa aynı yerel OCR motoruyla ikinci bir okuma yapılır: uzun tablo çizgileri okuma kopyasından temizlenir, başlıkların iki satıra bölünmesi desteklenir ve hücre kenarları yakın gerçek tablo çizgileriyle hizalanır. Kaynak dosya değişmez. İkinci deneme yalnızca daha fazla alan bulursa kullanılır ve kullanıcıya kontrol uyarısı bırakır.

Fatura/irsaliye numaraları ayrı değerlendirilir. Açıkça irsaliye olarak etiketlenen numaralar fatura numarası adayı olamaz. Fatura numarası etiketi okunmadığında, fatura tarihinin hemen üstündeki aday kontrol uyarısıyla gösterilir; daha aşağıdaki numaralar alınmaz.

Dövizli faturada ana toplamların altındaki farklı para birimli karşılıklar ana toplamların üzerine yazılmaz. Numara için tam sayfa/hücre okumaları uyuşmazsa tam sayfadaki aday kontrol uyarısıyla gösterilir; A/4 gibi karakterler yazılımla dönüştürülmez. Küçük tablo başlıkları gerektiğinde ayrı büyütülerek tekrar okunur.

Tablo çizgileri okunabiliyorsa kaçırılan ürün satırları gerçek yatay çizgilerden tekrar bölünür. Birleşik yazılan sütun başlıkları ayrıştırılır. Ürün adları ve alan adı gibi özel metinler OCR hatası içerebilir; bunlar tutarlılık hesaplarıyla doğrulanamaz ve kullanıcı incelemesi gerektirir.

## Faturayı listeden kaldırma

Faturalar sayfasında her satırın sağındaki çöp kutusunu kullanın. Onay penceresinde hangi faturanın kaldırılacağı gösterilir. İşlem onaylanınca kayıt listeden ve analizlerden çıkarılır. Bu işlem kaynak dosyayı ve geçmişi fiziksel olarak silmez; yerel denetim geçmişinde saklar. Okuması devam eden belgeler tamamlanana kadar kaldırılamaz. Filtreleri temizle düğmesi üst filtre alanının sağındadır.

Aynı firmanın farklı kalem sayısı ve sayfa yerleşimleri için firma adına bakarak sabit profil seçilmez. Web uygulamasında başlık ve konum eşleştirmesi kullanılır; eski komut satırı profil dosyaları ayrı kalır. Uzun açıklamalar tam satır bölgesinden, miktar/fiyat/KDV ise tutarın bulunduğu satır yüksekliğinden okunur.

Mac üzerinde, yalnızca numara harfini düşüren belirsiz okumada mevcut Apple Vision motoruyla numara hücresi ayrıca karşılaştırılır. Vision isteğe bağlıdır; Windows/Linux üzerinde bu ek adım yoktur ve çözülemeyen harf belirsizliği boş alan/uyarı olarak kalır. Bu adım dış API kullanmaz. Boş basılı tablo satırları mürekkep kontrolüyle ürün satırı sayımından çıkarılır.

## Hizmet bazında yeni fatura takibi

Faturalar tablosundaki hizmet adına tıklayın. Açılan sayfada ödenmiş fatura sayısı, kaynakta varsa başlangıç/bitiş dönemi, yıllık son hizmet bedeli grafiği ve bağlı yeni faturalar gösterilir. Yüklenen fatura iş akışı gereği ödenmiş sayılır; ödeme günü fatura tarihinden türetilmez. OCR tutarı kontrol edilip onaylanınca fiyat analizine katılır.

Yeni faturanın kalem açıklaması, ardından kalem adı ve fatura notu hizmet kataloğuyla eşleştirilir. Kurum ve para birimi de kontrol edilir. Birden fazla hizmete uyan veya bulunamayan açıklamada inceleme formundaki **Bağlı hizmet** alanını seçin; gerekirse **Yeni hizmet oluştur** ile kurumu ve açıklamayı tanımlayın. Tutar benzerliğinden hizmet tahmini yapılmaz.

Excel başlangıcındaki adetler ve bedeller korunur. Bu özellik açıldıktan sonra yüklenen faturalar eklenir; önceki PDF kayıtları ancak inceleme formunda açıkça bir hizmete bağlanırsa dahil edilir. Kaynak Excel'de bulunan fatura numarası yeniden yüklenirse başlangıç adedine tekrar eklenmez; aynı hizmette aynı numaralı yüklemeler de bir kez sayılır. Excel'in son fatura tarihinden eski PDF, kaynakta bulunan yıllık son bedeli değiştirmez. Yeni hizmetlerde onaylı faturalar fatura tarihine göre sıralanır. Silinen kayıt analizden çıkar.

Başlangıç dosyası özet tablo olduğu için tarihi bilinmeyen geçmiş faturalar tek tek oluşturulmaz. Hizmet türünün “Aylık” olması aktiflik kanıtı sayılmaz; açık durum bilgisi yoksa **Belirtilmedi** gösterilir. Geçmiş ayrıntılar paylaşılacak Excel ile tamamlanabilir. Hizmet kataloğu ve takibin başlangıç tarihi `data/reference/service-tracking.json` içinde saklanır; yedeğe data klasörünün tamamını dahil edin.

## Mükerrer fatura kontrolü ve numarayla arama

Yeni PDF'nin fatura numarası okunduğunda sistemdeki silinmemiş faturalarla karşılaştırılır. Aynı numaralı ikinci yükleme listeye ve hizmet analizlerine eklenmez; mevcut faturaya bağlantı gösterilir. Kontrol taslak kaydında ve onayda da yapılır. Eşzamanlı işlemler tek veritabanı yazma işlemi içinde denetlenir. Numara karşılaştırması büyük/küçük harf ve boşluk farkını kaldırır; harf/rakam karışıklığını tahminle düzeltmez.

OCR numarayı yanlış okuduysa **Numara yanlış okunduysa düzelt** ile gerçek numarayı girin. Kaydetmeden önce aynı kontrol tekrar yapılır. Numarası okunmayan belge inceleme bekler; eksik numarayla onaylanamaz. Silinen faturanın numarası tekrar kullanılabilir. Reddedilen yüklemenin kaynak belgesi ve okuma sonucu denetim için saklanır. Eski kayıtlar bu özellik eklenirken topluca değiştirilmez. Model laboratuvarında aynı faturayı farklı motorlarla karşılaştırma serbesttir.

Faturalar ekranındaki **Fatura numarasıyla ara** alanı yüklenen belgeler arasında arar. Numaranın tamamını veya bir bölümünü yazabilirsiniz. **Yüklenen faturalar** görünümünde de ayrı numara filtresi vardır; diğer filtrelerle birlikte çalışır. Excel özetindeki belgesi yüklenmemiş geçmiş faturalar bu belge aramasına dahil değildir.
