# Geliştirme Notları — Millennium Dawn +Turkey

Bu dosya modda ne yapıldığını, neden yapıldığını ve bir daha düşülmemesi gereken tuzakları tutar.
Workshop'a gönderilmez (senkronizasyon `NOTLAR.md`'yi hariç tutar). Her sürümde güncellenir.

## Temel bilgiler

| | |
|---|---|
| Ana mod (Workshop) | 3826896215 — "Millenium Dawn +Turkey (MD 2.0 Update)" |
| Türkçe dil paketi (Workshop) | 3827287270 — "Millenium Dawn +Turkey - Türkçe Dil Paketi" |
| Bağımlılık | Millennium Dawn 2777392649, sürüm 2.0.3 |
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

- **2.0.3-TUR.7** (31 Ekim 2026):
  - Enerji ve bor denge düzeltmeleri, odaklara yapay zekâ ağırlıkları (aşağıda "Açık işler").
  - 15 Temmuz: darbenin başarısız sonucu `TUR_fire_15_july_event` ve `coup_attempt_tur` bayraklarını koymuyordu; Turkey.363
    ve Turkey.126 hiç çıkamıyordu. Bağlandı.
  - Uzay Programı: Turkey.273 yorum satırındaydı, 5 karar sonsuza dek kilitliydi. Olay dağıtıcıya eklenerek açıldı (2023).
  - Laiklik kararı `UNLOCK_SECULARISM` arıyordu, ATA ağacı `UNLOCK_LAICISM` koyuyor. Düzeltildi.
  - Kürt federalizasyonu kararı, devam kararının aradığı bayrağı koymuyordu; Yumruk yolundaki gibi eklendi.
  - Türk Birliği: `TR_candidate` hiç koyulmayan `TURKIC_UNION_SIGNATURE` bayrağını bekliyordu; `TR_policies` artık koyuyor.
  - TKP aşı dalı CHP ağacındaki odağa bağlıydı (`TUR_buy_german_vaccines3`), `...11` yapıldı.
  - 55 okuma: `MAF/MIT/ANAS_government`, `ATA_NO_PR_ALLOWED`, `TUR_mafia_gone` ülke bayrağı olarak koyulup global
    okunuyordu. `TUR = { has_country_flag = X }` yapıldı; rejim koşulları ilk kez gerçekten çalışıyor.
  - `preppin_*` yazım hatası (`prepping_*`), metni olmayan 2 ipucu, çakışan `AYM_hungary_invest_3` odağı.
  - `release_check.py`: bayrak ve ağaçlar arası önkoşul kontrolleri (`tools/flag_allow.json`).
  - İmkânsız tarih pencereli 19 olay (`date > X` ve `date < X`, Turkey.508/509'da yıl hatası) bir aylık pencereye açıldı;
    olay ve dağıtıcı birlikte değişti.
  - Para: ipucuyla çelişen 39 yer düzeltildi. Gelir olarak anlatılıp para çıkaran odaklar (ANA_*, DSP, HEPAR, TECH) gelir
    oldu; Bitcoin alımı, Altın ve Koç gider oldu; ipucu yanlış olanlarda (Yunanistan yardımı, ECB/FED payı) ipucu değişti.
  - Partiler: `party_pop_array` 0–23'tür; `^24` satırları dizinin dışına yazıyordu. 57 yerde parti, yön veya oran metinle
    eşitlendi. `TUR_AKP_small_start1` istisna: kod %1 kaldı, metin %3'ten %1'e indi (kod değişseydi AKP üç kat hızlanırdı).
  - Meclis başlangıcı gerçek 18 Nisan 1999 sonucu: DSP 136, MHP 129, FP 111, ANAP 86, DYP 85, bağımsız 3 (CHP 0).
  - Turkeys.9207 (2022 ittifakı) +%20 yerine +%5; diğer kampanya olayları %1–5 arası.
  - PKK 2000 başlangıcına göre yeniden kuruldu (`TUR_pkk_timeline`, aylık). Sistem 2017'ye göreydi: `pkk_terror_idea`
    eklenmiyor, `pkk_presence` başlatılmıyor, saldırganlık yalnızca düştüğü için "ateşkes bozulması" tetiği çalışmıyordu.
    2000: Öcalan sonrası ateşkes, güç 35 → 20, saldırganlık 45 → 30, rastgele saldırı yok. Haziran 2004: düşük yoğunluk
    başlar, 38 karar açılır, varlık 30'dan başlar (üst sınır 60). Temmuz 2015: barış süreci biter, saldırganlık 70'e
    çıkar ve kendiliğinden söner. Cezalar: toplam -%9 istikrar / -%6 siyasi güç (2015 zirvesinde -%12). Düşük yoğunlukta
    saldırı yaklaşık 7 ayda bir. `add_stability = -0.5` yazım hatası -0.05 yapıldı.
  - Oyun içi test geri bildirimi: 70 günlük Türkiye odakları kısaldı. Savaş, rejim, yol seçimi ve büyük ödüllü olanlar
    55 gün (`7.86`), diğerleri 45 gün (`6.43`); 20 günlükler 21 gün. 35 ve 50 günlükler aynı. Mafya olayı haftalık %50'den
    %20'ye indi, üçüncü seçenek 10 yerine 3,5 milyar. Cumhurbaşkanlığı ekranı adayların adını, partisini ve seçilirse
    vereceği etkiyi gösteriyor. ANAP artık "Libertarians" görünmüyor. Üretici fonları AAT DLC'si yoksa ordu tecrübesi
    veriyor. TUSAŞ'ın helikopter üreticisi için eksik MIO eklendi.
  - Borç 364, hazine 34 ve kişi başı GSYH MD'nin değerleri, değiştirilmedi.
  - `release_check.py`: imkânsız tarih, hazine/ipucu ve dizi dışı parti kontrolleri.
  - `FIRE_SUPEREVENT_13` ("Turkish Germany") bilinçli olarak açılmadı: onu tetikleyecek içerik hiç yazılmamış.

- **2.0.3-TUR.8** (31 Ekim 2026), Atatürk güncellemesi:
  - Atatürk yolu kilitleniyordu: `ATA_declare_elections` MD'nin seçim kampanyasını açıyordu, CHP kazanamıyor, ağaç
    `western_social_democrats_are_in_power` bekliyordu. Artık CHP'ye +%25 ve `change_ruling_party_effect` (rul_party 3).
    TurkeyF.207 seçimleri kapatıp CHP'yi iktidara alıyor. `ATA_new_kemalism` gerçekten CHP'yi +%3 artırıyor.
    `ATA_a_new_control`'ün o noktada sağlanamayan `available`'ı kaldırıldı. Oyunda doğrulandı.
  - Buff: `ATA_came_back` +150 PP, 3 yıllık `ATA_return_of_the_father`, 7 bölgede 10 sivil / 8 askerî / 2 tersane (slotlarıyla).
    Odaklardaki 41 fabrika/tersane ve 5 offsite iki katı (ek slotla), 36 PP ödülü 1,5 katı.
  - Yol Rehberi 10 sayfa (`custom_opening_2..11`, `FAQ_1..10`), her yolun tarih aralığı ve bekleme süreleri.
  - Tekrarlanan bloklar: HOI4 yalnızca sonuncusunu okur. 48 odakta `available`, 5 TMSF kararı ve uçak projesinde
    `remove_effect`, `TUR_clear_the_slums`'ta `complete_effect` birleştirildi; `TUR_ottoman_rally`'deki ölü ilk üçlü silindi.
  - Var olmayan `cost_reduced_last_stand` ipuçları (OTT, TKF) ve `TKF_beat_the_EMEPs_coup`'taki ölü koşul kaldırıldı.
- **2.0.3-TUR.9** (1 Kasım 2026):
  - Odak süreleri: 21 günlük odaklar 30, 45 günlükler 50 gün (AKP kuruluş olayları 16 Ağustos 2001'de geliyordu, ağaç
    öne geçiyordu). Özel ağaçlardaki 105 günlük 44 odak 65 gün (`cost = 9.29`). TSK'daki 210 günlük odak bilerek kaldı.
  - Cumhurbaşkanlığı seçimleri 45/55 (2000), 58/42 (2007), 52/48 (2014) başlıyor. Aday ipuçlarındaki ham `$KEY$` metni:
    scripted loc iç içe anahtarı açmıyor, metin doğrudan yazıldı. Mafya seçeneği 1,5 milyar.
  - Türkçe ekipman adları (`TUR_equipment_names_l_english.yml`): tank gövdeleri, helikopterler, Türksat/Göktürk/UKZS.
    Teknoloji adları ülkeye özel yapılamıyor: araştırma ekranı `[scripted loc]` çalıştırmıyor, ham parantez gösteriyor (test edildi).
  - Bilim insanı portreleri: `portraits/999_TUR_scientist_portraits.txt`, 26 erkek 13 kadın, militan portre yok.
  - Atatürk'ün Mirası Korunuyor: +%10 istikrar, +0.50 PP; Tamamlandı: +0.75 PP. İsimsiz 8 ruha isim.
  - Genel adla görünen partiler (`00_MD_politicsview_scripted_localisation.txt`, TUR yedek satırları `TUR.<ideoloji>_2000`):
    LDP, ÖDP, Türk Hizbullahı, Kitap ve Sünnet Cemaati, İBDA-C, Yeşiller, SHP, Yenilikçiler. BBP zaten başka slotta var.
  - Yalnızca ipucu gösteren 20 odak: Mafya soygunları yeni karar kategorisi (`TUR_mafia_heists`), Anarşist (çekirdek,
    savaş hedefi, komünizm desteği), DEM (+%10 istikrar), DSP (parti desteği), MHF (gizli plan ruhu, ittifak görüşü,
    BOS/ALB ittifaka). Rus kimyasal test odağı ABD'ye bakıyordu, SOV oldu.
  - Workshop başlık/açıklaması 12 dilde (`tools/workshop/i18n/`), Steam'in Edit Title & Description sayfasından.
- **2.0.3-TUR.9.1** (1 Kasım 2026), düzeltme: İngilizce oyunda Türkçe kalan girdiler çevrildi (yeni parti adları,
  Özel Kuvvetler Komutanlığı, MIST/MIDST ruhları, senfoni orkestrası ruhu, Turkey.254.a), "Arınç" yazımı düzeltildi.
  Tarama: oyunda kullanılan her odağın İngilizce açıklaması var; boş 758 `_desc` anahtarının odakları yorum satırında.

- **2.0.3-TUR.9.2** (1 Kasım 2026), parti isimleri düzeltmesi: scripted localisation dosyasının başındaki
  UTF-8 BOM kaldırıldı. Bu üç bayt bütün parti isimlerini ve logolarını boş bırakıyor, 312 ayrıştırma hatası
  üretiyordu. Yeni oyun oturumunda isimler ve logolar doğrulandı; ilgili hata sayısı sıfır. Yayın kontrolü artık
  scripted localisation içindeki BOM'u da reddediyor; 5 regresyon testi eklendi. Mevcut kayıtlarla uyumludur.

- **2.0.3-TUR.10** (2 Kasım 2026), Türkçe dil güncellemesi ve denge: diplomatik tur odaklarının yabancı ülkelere
  verdiği siyasi güç/istikrar Türkiye'ye alındı (ziyaret edilen ülkeye +20 görüş, `TUR_diplomatic_tour`), TKF
  seferberliği 500 bin, nüfus projesi %50, anarşist bilim %15, PP ödülleri 325/275/250/250, dört zayıf yolun ilk
  odakları güçlendirildi. 44 yeni ikon (toplam 559). Dil paketi: MD arayüzü/mekanikleri, AB (`MD_focus_EU`) ve
  Orta Doğu (`MD_middle_east_content`) çevirisi `zz_TR_MDX2_*` dosyalarında; paket 64.241 satır. Yükleme ekranı ve
  yükleme ipuçları ASCII (yazı tipi ı/ş/ğ içermiyor, oyunda doğrulandı).

- **2.0.3-TUR.11** (3 Kasım 2026), tarih güncellemesi:
  - 2023 seçimi oyuncu seçimi değil: ittifakların parti desteği, gerçek sonuç ve istikrardan hesaplanıyor
    (`common/scripted_effects/TUR_2023_election_effects.txt`, `gen_effects.py` ile üretildi). Zafer odakları yalnızca
    kazanana açılıyor (`TUR_2023_winner_*`), seçim hiç olmazsa 1 Temmuz 2023'ten sonra eski davranış. ATA İttifakı olayı
    (742), İnce'nin yarışta kalması (743, Memleket > %6), Oğan pazarlığı seçimli, Özdağ protokolü bayrakla tutuluyor.
  - Özgür Özel CHP kurultayının dördüncü sonucu (`CHP_ozgur_ozel`); 38. Kurultay 4–5 Kasım 2023'e taşındı.
  - 24 yeni tarihî olay (Turkey.742–765): Çözüm Süreci, 2015'in iki seçimi, Rus yaptırımları (`TUR_russian_sanctions`),
    Esad'ın düşüşü, Terörsüz Türkiye, Fırat Kalkanı, Barış Pınarı, Pençe-Kilit/Kılıç, İsrail ticareti, tahıl koridoru,
    Kasım 2002 sonucu, Brunson'ın tahliyesi. Brunson yaptırımı varsa Ağustos 2018 kur olayı (270) daha sert.
  - Tarih düzeltmeleri: Su-24 krizi 24 Kasım 2015; 2010 ve 2017 referandum sonuçları gerçek tarihlerde (dağıtıcıdan,
    kararlar artık olayı doğrudan çağırmıyor); yemin töreni (314) Temmuz 2018'e taşındı ve referandum gerekiyor.
  - Yeni odaklar: "Oğan Hükümette mi?" (Erdoğan), "İçişleri Bakanı Özdağ" ve "Masanın Çatlakları" (Kılıçdaroğlu),
    olaylar 766 ve 767. 72. satırda, çünkü 70. satır dolu.
  - Atatürk yolu: 40'tan az fabrika şartı (Türkiye ~66 ile başlıyor), darbe olaylarından korunuyor, açılış güçlendi.
    Ecevit görevi zaman aşımında oyuncu artık Azerbaycan'a geçmiyor.
  - Yol Rehberi 15 sayfa, hoş geldiniz penceresini yeniden açan karar.
  - Dil paketi: yeni içeriğin hepsi Türkçe; ı/ş/ğ içeren 26 olay başlığı yazı tipi kuralına çevrildi.
- **2.0.3-TUR.12** (3 Kasım 2026), teçhizat ve ikon güncellemesi:
  - Çökme: Türk Birliği dalındaki `TR_launch_a_coup` ödülünde `ruling_party` olmadan `set_politics` vardı (93a15ba).
    Odak ipucu yazılırken oyun çöküyordu (yığın exe içinde çözüldü: odak ipucu → EFFECT_SET_POLITICS → parti adı).
    MD'nin `enable_elections_with_no_leader_change` efekti kullanılıyor. `set_politics` her zaman `ruling_party` ister.
  - Teçhizat isimleri: `TUR_equipment_names_l_english.yml` (yeni anahtarlar) ve
    `replace/TUR_equipment_replace_l_english.yml` (MD'nin ABD'den kopyalanmış TUR_ isimleri).
  - 325 yeni odak ikonu: `tn_837`–`tn_1161`, `interface/TUR_focus_icons_2026.gfx`.
- **2.0.3-TUR.13** (9 Kasım 2026), ekonomi ve iktidar kilidi:
  - 2001 çöküşü: MD'nin kurtarma odağı ve "Ekonomik Felaket" sekmesi alt modda yoktu, "Ekonomik Plan Yok" hiç kalkmıyordu.
    `common/decisions/TUR_economic_recovery.txt` (kurtarma kararı + geri getirilen `TUR_incoming_collapse` görevi,
    `TUR_economic_crisis_over_done` bayrağına bakar), `TUR_economic_insecurity3`.
  - Atatürk kilidi: `TUR_ata_power_lock.txt`, aylık `ATA_power_lock_check` (`on_monthly_TUR`), olay `ATA_lock.1`.
    Yolu açan her yer `ATA_start_power_lock` çağırır, seçimler kapalı kalır.
  - Askerî ağaç kilidi (`MD_TUR_MIL`, `MD_TUR_TSK`): `TUR_junta_power_lock.txt`, olay `ATA_lock.2`; MIL'de
    `TUR_open_elections` odağıyla biter.
  - `release_check.py`: `set_politics` her zaman `ruling_party` ister; Atatürk yolunu açan her yer kilidi başlatır;
    `has_focus_tree` modun bir ağacını adlandırır.

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
- **`common/scripted_effects`, `scripted_triggers` ve `scripted_localisation` dosyalarında BOM olmaz.** Ayrıştırıcı, yorumla başlayan
  dosyanın önündeki BOM'u reddediyor (dağıtıcı bu yüzden bir kez yüklenmedi). Yerelleştirme `.yml` dosyalarında ise BOM şart.
- **Satır sonları:** repo CRLF (autocrlf=true), MD dosyaları LF. 3-yollu birleştirmeden önce normalize edilir (`md_sync.py` yapıyor).
- **MD API:** `change_*_opinion` efektlerini çağırmadan önce `set_temp_variable = { temp_opinion = X }`.
  MD bazı şeyleri `meta_effect` ile dinamik çağırır (`set_leader_[TAG]`), bunlar aramada "kullanılmıyor" görünse de silinmez.
- **"Kullanılmıyor" demeden önce yazım hatalarına bak.** `TurkeyF.200s` gibi bir yazım hatası, gerçekten kullanılan bir
  olayı ölü gösterebilir. Silmeden önce benzer kimlikleri ara; artık `release_check.py` olmayan olay çağrılarını yakalıyor.
- **Türkçe paket başlıkları:** olay ve GUI başlık fontlarında ı/ş/ğ glifi yok. Bu başlıklarda harfler
  i/s/g'ye çevrildi (942 satır). Gövde metinleri normal Türkçe.
- **`has_global_flag = Inevitable` hata değildir:** hiç koyulmayan bayrak, görevin süre dolana kadar açık kalmasını sağlayan
  kasıtlı kalıptır (`timeout_effect` çalışır). Böyle bayraklar `tools/flag_allow.json`'a yazılır.
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
   Dil paketi için `python tools/md_loc.py`: MD'nin İngilizcesi değişen çevirileri ve çevrilmemiş yeni MD satırlarını
   listeler. Çevirdikten sonra `python tools/md_loc.py snapshot` ile taban kaydı yenilenir ve `md_loc_base.json` commit'lenir.
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
