# Geliştirme Notları — Millennium Dawn +Turkey

Bu dosya modda ne yapıldığını, neden yapıldığını ve bir daha düşülmemesi gereken tuzakları tutar.
Workshop'a gönderilmez (senkronizasyon `NOTLAR.md`'yi hariç tutar). Her sürümde güncellenir.

## Temel bilgiler

| | |
|---|---|
| Ana mod (Workshop) | 3826896215 — "Millenium Dawn +Turkey (MD 2.0 Update)" |
| Türkçe dil paketi (Workshop) | 3827287270 — "Millenium Dawn +Turkey - Türkçe Dil Paketi" |
| Bağımlılık | Millennium Dawn 2777392649, sürüm 2.0.2 |
| Oyun | HOI4 1.19.3 (`supported_version="1.19.*"`) |
| Repo | bu klasör, ana dal `master`, her sürüm `v<sürüm>` etiketiyle |
| Yükleme klasörü | `Belgeler\Paradox Interactive\Hearts of Iron IV\mod\md_turkey_upload` |
| Paket klasörü | `...\mod\md_turkey_tr` (kaynağı repodaki `turkish_pack/`) |

## Sürüm geçmişi

Ayrıntılı değişiklik notları Steam'deki **Change Notes** sekmesinde (açıklamaya changelog yazılmaz).

- **2.0.2-TUR** (25 Ekim 2026): Orijinal mod (MD 1.12.3A / HOI4 1.17) MD 2.0.2 ve HOI4 1.19.3'e taşındı.
  Kırık parantezler, eski MD API'leri, kayıp olay/ruh/odak referansları, ölü dosyalar, yerelleştirme hataları
  (~10 bin İngilizce metin düzeltildi). Yeni Workshop öğesi 3826896215 açıldı, Türkçe dil paketi 3827287270 yayınlandı.
- **2.0.2-TUR.2** (26 Ekim): Performans. Her gün her ülke için kontrol edilen 749 "polled" Türkiye olayı
  "triggered" yapıldı. Bunları günde bir kez yalnızca Türkiye için kontrol eden dağıtıcı eklendi
  (`common/scripted_effects/TUR_polled_event_dispatcher.txt`, `on_daily_TUR`'dan çağrılır). Hızlı düzeltmeler: eksik parantez,
  olay kapsamı, tetik sırası.
- **2.0.2-TUR.3** (26 Ekim): İç fraksiyon görüş değişiklikleri hiç çalışmıyordu (124 yer).
  MD 2.0.2'de çağıran `temp_opinion` ayarlamalı; mod `temp_opinion_change` ayarlıyordu. Düzeltildi. MD'nin
  dosyalarını gölgeleyen 16 dosya için `tools/md_sync.py` eklendi.
- **2.0.2-TUR.4** (26 Ekim): Hiçbir şeyin tetiklemediği 38 olay çözüldü: 7 ret cevabı bağlandı, 7 tarih/koşul olayı
  dağıtıcıya eklendi, 3 odak ödülü ve 1 haber bağlandı, 17 ölü olay ve 26 kullanılmayan ruh silindi.
- **2.0.2-TUR.5** (27 Ekim, ana mod ve Türkçe paket birlikte yayınlandı):
  - 1.440 odak grubu için İngilizce ve Türkçe açıklamalar (2.097 odak).
  - Yayın öncesi kontrol aracı (`tools/release_check.py`) ve onun bulduğu hatalar:
    - "Askerî Dram" olayının B seçeneği yazım hatası yüzünden (`TurkeyF.200s`) "Mahkeme Yönetimi Devralıyor"
      olayını tetikleyemiyordu. TUR.4'te bu olay yanlışlıkla "ölü" sanılıp silinmişti; geri getirildi ve bağlandı.
    - S-400 olayının tetiklediği "ABD Türkiye'yi F-35 Programından Çıkardı" (Turkey.340) yorum satırı hâlindeydi; açıldı.
    - Savaş tezkeresi oylamasının "kabul" sonucu (TurkeyT.19) hiç yazılmamıştı; yazıldı. 70 gün Meclis'e sormadan savaş ilanı.
    - Afrin kararı hiçbir sürümde var olmamış `TUR_ob_warn.1` olayını çağırıyordu; çağrı kaldırıldı.
    - `has_idea = fascism` → `has_government = fascism` (fascism bir ideoloji, ruh değil).
    - 36 sprite var olmayan resim dosyasına bakıyordu (.png/.dds uzantı değişiklikleri, MD'de taşınan dosyalar);
      hepsi var olan dosyalara bağlandı, kullanılmayan 4 olay resmi tanımı silindi.
    - 3 eksik sprite adı (MD, vanilla'nın goals.gfx/ideas.gfx dosyalarını değiştirdiği için yok olanlar) düzeltildi.
    - 4 bozuk yerelleştirme satırı ve 10 çift tanımlı anahtar (5'i Türkçe pakette) düzeltildi.
  - `MD_source/` (PSD şablonları) yanlışlıkla Workshop'a gidiyordu; senkronizasyondan çıkarıldı.

- **2.0.3-TUR.6** (28 Ekim, ana mod ve Türkçe paket birlikte yayınlandı; MD 2.0.3 için):
  - Mod çakışması uyarısı: başka bir mod Türkiye'nin ülke geçmişini (`history/countries/TUR - Turkey.txt`) ezerse
    (genelde ikinci bir Türkiye modu) yeni oyunun başında uyarı penceresi çıkar
    (`common/scripted_guis/TUR_load_order_warning.txt`, `interface/TUR_load_order_warning.gui`). Bizim TUR geçmişi
    `TUR_submod_history_loaded` bayrağını koyar; `on_startup` bayrak yoksa `TUR_load_order_wrong` koyar. Yalnızca yeni
    oyunlarda kontrol edilir; eski kayıtlarda yanlış alarm vermez. Oyunda test edildi: normal kurulumda pencere çıkmaz,
    bayrak satırı kaldırılınca Türkçe pencere çıkıyor ve "Anladım" ile kapanıyor.
  - Millennium Dawn 2.0.3 ile uyumlu: gölgelediğimiz 16 dosya değişmemiş (`md_sync status`), referans kontrolü temiz;
    `md_overrides.json` `base_version` 2.0.3.
  - Kalan 28 polled olaydan 7'si (Türkiye'nin var olmasını gerektirenler) dağıtıcıya taşındı. Turkey.597'nin (Kürecik
    radarı) tarih aralığı boştu (2012.2.7–2012.2.7), hiç çıkamıyordu; düzeltildi. Kalan 21'i bilerek polled: tetikleri
    Türkiye olmadan da geçerli (iç savaş etiketleri, tüm ülkelere giden COVID olayı, gerçek rastgele süreli PKK olayları,
    ABD/SSCB/PAN tepkileri) ve hepsi önce `tag = X` kontrol ettiği için maliyetleri ihmal edilebilir.
  - Kontrol aracı: bilinmeyen modifier adı (oyunun kendi dokümantasyonuna ve tüm katmanların modifier_definitions'ına
    göre), MD'nin aynı modifier için kullandığı en yüksek değeri aşan değerler (denge), yanlış kapsamda çalışan
    efektler; commit öncesi hook (`git config core.hooksPath tools/hooks`). `strip_code` regex'e geçti (10 kat hızlı).
  - `army_org_Factor` → `army_org_factor` (31 yer; oyun büyük/küçük harfe duyarsız, yalnızca tutarlılık).
  - Kalan tüm odak açıklamaları yazıldı: 2.580 grup, 2.642 odak, İngilizce ve Türkçe (`tools/focus_desc/round2/`).
    Artık ağaçlardaki her odağın açıklaması var. Karanlık içerikli odaklar (terör, katliam, ırkçı politikalar)
    hikâye düzeyinde ve kınayan bir dille anlatıldı. Kalan boş `_desc` anahtarları yorum satırına alınmış odaklara ya da
    hiçbir odağın kullanmadığı anahtarlara ait. `MIT_balkan_inluence_program_desc` iki dosyada tanımlıydı; biri silindi.

## Kalıcı dersler (tekrar düşme!)

- **Sesler WAV kalmalı.** HOI4 ses efektlerini yalnızca WAV'dan yükler. OGG'ye çevirince (88d1f8e) 22 konuşma
  sessiz kaldı, WAV'a geri dönüldü (c4fbe45). Boyut küçültmek için örnekleme hızı/kanal düşürülür, format değişmez.
- **Workshop kopyası açılmıyorsa önce `logs/system.log`'a bak.** "Active Mod Count" ve "Active Mod:" satırları
  oyunun gerçekten neyi yüklediğini gösterir. Bu bilgisayarda local `md_turkey_upload.mod` ve `md_turkey_tr.mod`
  dosyaları Workshop öğeleriyle aynı `remote_file_id`'yi taşıdığı için oyun Workshop kopyalarını sessizce atlıyordu.
  O iki dosya `mod_disabled_test\` klasöründe durur. Yalnızca launcher'dan yükleme yaparken `mod\`'a geri konur,
  yüklemeden sonra yine çıkarılır. (CreamAPI ya da yükleme sırası suçlanmıştı; ikisi de bu belirtinin sebebi değildi.)
  Aboneleri etkilemez, onlarda local kopya yok.
- **MD ile +Turkey'nin playset sırası modu bozmaz.** 28 Ekim'de denendi: `dlc_load.json`'da MD en sonda olsa bile
  bizim aynı yoldaki TUR geçmiş dosyamız kazandı (kayıtta `TUR_submod_history_loaded` vardı). Oyun bir modu
  `dependencies` satırındaki modlardan sonra yüklüyor. Önceden "MD sonra yüklenirse odak ağacı kaybolur" denmişti; bu
  yanlıştı ve 2.0.2-TUR.5 değişiklik notunda da geçiyor. Gerçek risk, Türkiye dosyalarını değiştiren başka bir modun
  bizden sonra gelmesi; TUR.6'daki uyarı penceresi bunu yakalıyor.
- **`common/scripted_effects` ve `scripted_triggers` dosyalarında BOM olmaz.** Ayrıştırıcı, yorumla başlayan
  dosyanın önündeki BOM'u reddediyor (dağıtıcı bu yüzden bir kez yüklenmedi). Yerelleştirme `.yml` dosyalarında ise BOM şart.
- **Satır sonları:** repo CRLF (autocrlf=true), MD dosyaları LF. 3-yollu birleştirmeden önce normalize edilir (`md_sync.py` yapıyor).
- **MD API:** `change_*_opinion` efektlerini çağırmadan önce `set_temp_variable = { temp_opinion = X }`.
  MD bazı şeyleri `meta_effect` ile dinamik çağırır (`set_leader_[TAG]`), bunlar aramada "kullanılmıyor" görünse de silinmez.
- **"Kullanılmıyor" demeden önce yazım hatalarına bak.** `TurkeyF.200s` gibi bir yazım hatası, gerçekten kullanılan bir
  olayı ölü gösterebilir. Silmeden önce benzer kimlikleri ara; artık `release_check.py` olmayan olay çağrılarını yakalıyor.
- **Türkçe paket başlıkları:** olay ve GUI başlık fontlarında ı/ş/ğ glifi yok. Bu başlıklarda harfler
  i/s/g'ye çevrildi (942 satır). Gövde metinleri normal Türkçe.
- **Clausewitz anahtarları büyük/küçük harfe duyarsızdır** (`SpriteType`, `army_org_Factor` çalışır). Kontrol aracı
  modifier adlarını bu yüzden küçük harfle karşılaştırır.
- **Denge uyarıları tasarım kararıdır**: `release_check.py` MD'den güçlü değerleri listeler ama otomatik düzeltilmez.
  İncelenip bilinçli bırakılanlar `tools/balance_allow.json`'a yazılır.
- **İngilizce metinlerde ı ş ğ İ Ş Ğ kullanılmaz** (Latin-1 dışı, İngilizce fontlarda olmayabilir). ü ö ç sorun değil.
- **Oyunu test için doğrudan başlat:** `hoi4.exe`'yi çalışma dizini oyun klasörü olacak şekilde çalıştır. Hangi
  modların yükleneceği `dlc_load.json`'dan okunur; launcher bu dosyayı yeniden yazabilir, testten önce kontrol et.
- **Yükleme yolu:** tek oyunluk launcher (`steam://rungameid/394360`) → Mod kitaplığı → MOD YÜKLE → modu seç →
  Steam Workshop → MOD YÜKLE. Bu yol açıklama kutusundaki metni Steam'e yazar (önceden dolu gelir, olduğu gibi bırakılır).
  Ardından Steam'de öğe → Change Notes → yeni boş notu Edit ile doldur. Açıklamaya changelog yazılmaz; açıklamadaki
  "Resmî Türkçe Dil Desteği" bölümü korunur.

## Yayın kontrol listesi

1. `python tools/md_sync.py` (MD güncellendiyse önce `merge`/`accept`). MD güncellemesinde sıra:
   `status` → `merge` → çakışmaları çöz / replace dosyalarını incele → `accept` → `release_check.py` → oyunda test →
   `md_base/` ile birlikte commit. `md_overrides.json`'daki `base_version` güncellenir (2.0.3'e geçişte hiçbir dosya
   değişmedi, yalnızca etiket güncellendi).
2. `python tools/release_check.py` — 0 hata olmalı. Uyarılar okunur, bilinçli olanlar dışında düzeltilir.
3. `descriptor.mod` ve gerekiyorsa `turkish_pack/descriptor.mod` içinde `version=` artırılır.
4. Senkronizasyon (PowerShell):
   ```
   robocopy "<repo>" "$mod\md_turkey_upload" /MIR /XD .git turkish_pack _archive .claude _workshop_gallery .vscode tools MD_source /XF .gitignore NOTLAR.md
   robocopy "<repo>\turkish_pack" "$mod\md_turkey_tr" /MIR
   ```
   `/XD` ile hariç tutulan klasörler hedefte zaten varsa robocopy onları silmez. Elle silinir (`MD_source` gibi).
5. Oyunda yükleme testi: `release_check.py`'nin "log" bölümü son oturumda modun gerçekten yüklendiğini ve
   `error.log`'da moddan hata olmadığını gösterir.
6. Commit, `v<sürüm>` etiketi.
7. Local `.mod` dosyalarını `mod\`'a koy → launcher'dan yükle → Change Notes'u doldur → `.mod` dosyalarını yine çıkar.

## Araçlar (`tools/`, Workshop'a gitmez)

- `release_check.py`: yayın öncesi kontrol. Vanilla + MD (`replace_path` dahil) + mod katmanlarını oyunun yaptığı gibi
  birleştirip olay/ruh/odak/sprite/ses/yerelleştirme referanslarını, dosya kodlamalarını, Türkçe paketi (yetim satır,
  `$değişken$`/`[scripted loc]`/`£ikon` kaybı, kapsama), yükleme klasörlerinin repo ile eşitliğini, Workshop'u gölgeleyen
  local `.mod` dosyalarını, MD senkronunu ve son oyun oturumunun loglarını denetler. `--all`, `--strict`,
  `--report dosya.md`, `--only refs,loc` seçenekleri var.
- `md_sync.py` + `md_overrides.json` + `md_base/`: MD'nin gölgelediğimiz dosyalarını MD güncellemeleriyle eşitler.
- `convert_events.py`: polled olayları triggered + dağıtıcıya çevirir (TUR.2'de uygulandı).
- `focus_desc/`: boş odak açıklamaları için iş hattı. `extract.py` grupları ve partileri üretir, açıklamalar
  `out/dNNN.txt` dosyalarına `no ||| İngilizce ||| Türkçe` olarak yazılır, `build.py check` doğrular,
  `build.py apply .` modla pakete yazar. `groups.json` partilerin hangi odaklara denk geldiğini tutar. **Yeniden
  `extract.py` çalıştırmak numaraları değiştirir**; yeni partiler yazmadan önce yeniden çıkarılır ve eski `out/` saklanır.

## Açık işler

- Odak açıklamaları tamamlandı (TUR.5'te 1.440 grup, TUR.6'da 2.580 grup). Oyunda göz ile kontrol edilmedi.
- Odak adları üzerine tasarım kararı: "Secret Jewish Mind Games", "Jewish Gold", "Counter the Jewish Lobby" gibi
  antisemitik kalıp taşıyan başlıklar orijinal moddan geliyor. Açıklamalar bunu eleştirel anlatıyor. 28 Ekim'de
  karar: başlıklar olduğu gibi kalacak (Steam'de şikâyet riski bilinerek).
- Yapay zekâ odak ağırlıkları `tools/add_ai_weights.py` ile eklendi (31 Ekim, henüz yayınlanmadı): önce ekonomi ve
  araştırma, sonra güvenlik, savaş ve ilhaklar en sonda. Gözlemci modunda davranış hâlâ test edilmedi.
- Performans ölçümü (TUR.2 olay optimizasyonunun etkisi) yapılmadı.
- Denge (31 Ekim'de gözden geçirildi): "MD en fazla" sütunu yalnızca bulunan en yüksek değeri gösterir, ölçek değildir.
  `decryption_power` MD'nin istihbarat özelliklerinde 50'ye çıkıyor; `country_resource_cost_*` düz tüketim birimi.
  Gerçek hata enerjideydi: aynı etki hem yüzde (`fossil_pp_energy_generation_modifier = -1.0`) hem düz değer
  (`fossil_energy_gain = -100`) yazılmıştı. Düz değer santral üretimini eksiye düşürebilir ve MD'nin kuralına aykırıdır.
  5 düz değer silindi, `nuclear_energy_gain = -10` → `nuclear_energy_generation_modifier = -0.10`, bor -60/-25 → -15/-11.
  Kalanlar `tools/balance_allow.json`'da; yeni değerler uyarı vermeye devam eder.
