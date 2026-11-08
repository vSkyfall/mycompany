# Örnek koşu kaydı — okuma rehberi

Bu klasörde gerçek bir koşunun anonimleştirilmiş kaydı var:
[kosu-kaydi.md](kosu-kaydi.md) — `x-icerik` takımı, 11 Eylül 2026, 17:16.

Koşu kayıtları normalde repoya girmez (`.gitignore` → `takimlar/*/kosu/`). Bu tek kayıt
örnek olsun diye buraya kopyalandı; X hesap adı `<hesap>`, tweet id `<id>` ile değiştirildi.
`update_id` değerleri olduğu gibi bırakıldı — kişisel veri taşımazlar, Telegram'ın kendi sayaçlarıdır.

---

## Koşu kaydı nedir, neden zorunlu

> **ANAYASA §4:** Her koşu `SIRKET_KOSU` yoluna kayıt yazar: ne okundu, ne üretildi, ne kaldı,
> kaç USD. **Kayıtsız koşu reddedilir.**

Ajanın hafızası yoktur; oturum kapanınca her şey gider. Geriye yalnız yazdıkları kalır.
Koşu kaydı üç işi birden görür:

1. **Denetlenebilirlik.** Bekçi kaydı okur ve ona göre karar verir — kayıt ajanın savunmasıdır.
   Boş kayıt otomatik red'dir ([../03-bekci.md](../03-bekci.md)).
2. **Muhasebe.** Altbilgideki `maliyet: N USD` satırı günlük bütçenin sayıldığı yerdir
   (`dagitici.gunluk_maliyet`). Kayıt silinirse muhasebe de silinir.
3. **Hafıza.** Bir sonraki koşu `kosu/` klasörüne bakarak dün ne olduğunu öğrenir.

Dosya yolu: `takimlar/<takim>/kosu/YYYY-MM-DD-HHMM.md`. Adı `kos.kosu_yolu()` üretir; dağıtıcı
"bugün kaç koşu oldu" sayarken ve `gunluk.py` raporu yazarken **dosya adını** ayrıştırır,
o yüzden ad biçimi serbest değildir.

---

## Bu kayıt nasıl oluştu

```
Telegram'a link atıldı
        │
        ▼
bin/telegram_dinle.py   long-poll turu mesajı yakaladı
        │               → takimlar/x-icerik/gelen/2026-09-11-30760581.json
        │               → durum.json kuyruğuna x-30760581 (bekliyor)
        │               → dagitici.tetik_karari() izin verdi (mesai içi, kuyrukta iş var)
        ▼
bin/kos.py x-icerik     .env → kilit → mesai → agents üret → anahtar kontrolü → istem
        │               → claude -p --model sonnet --max-budget-usd 2
        │                  ortamda SIRKET_TAKIM=x-icerik, SIRKET_KOSU=<bu dosya>
        ▼
ajan koşar             ANAYASA → AJAN-KIMLIGI → kurallar → takim.md → skills
        │              takim.md adımlarını sırayla uygular, kaydı yazar
        ▼
Stop hook → bin/bekci.py    ön kontrol (temiz) → LLM denetimi → "kabul"
        │                   kararı kaydın altına + durum.json + bekci-telemetri.jsonl
        ▼
kos.py altbilgiyi ekler     - maliyet: 0.388 USD · tur: 19 · hata: False
        │
        ▼
durum.json                  son_kosu, son_sonuc: "tamam"
```

Tetik yollarının tamamı [../02-dongu.md](../02-dongu.md)'de.

---

## Bölüm bölüm

Kayıt serbest metindir — sabit bir şablonu yoktur. Zorunlu olan tek şey `takim.md`'nin
son adımında yazan içeriktir: *ne okudun, ne ürettin, ne kaldı, hangi kaynaklardan, kaç USD.*
Bu örnekteki bölümler o sözleşmeyi karşılamanın pratik bir yoludur.

### Başlık

```markdown
# Koşu kaydı — x-icerik — 2026-09-11 17:16
```

Takım ve zaman. Sürücü kaydı ajan hiç yazmamışsa kendi açar ve başına kendi üstbilgisini
koyar (`# Koşu — <takim> — <zaman>` + model/bütçe satırı + `**Ajan koşu kaydı yazmadı.**`).
Yani bu başlığı görüyorsanız kaydı **ajan** yazmıştır.

### `## Okunanlar`

Koşuda hangi dosyaların açıldığı. Üç öbek görünüyor: çerçeve dosyaları (ANAYASA →
AJAN-KIMLIGI → kurallar → takim.md, yani [okuma sırası](../01-nasil-calisir.md)), o adımda
gereken üç yetenek dosyası, ve takımın kendi hafızası (`defter.md`, `durum.json`).

Bu bölüm iki şeyi ölçülebilir kılar: ajan okuma sırasına uydu mu, ve gereksiz dosya okuyup
token yaktı mı. `sirket/AJAN-KIMLIGI.md`'nin verimlilik kuralı bunu söyler:
*"gereksiz dosya okuma, ham log yapıştırma, aynı aramayı iki kez yapma."*

### `## Adım N — …` başlıkları

Kaydın gövdesi `takim.md`'deki **koşu adımlarını** takip eder. Bu örnekte adımlar
gruplanmış: "Adım 1 — girdi", "Adım 2-3 — çekim ve doğrulama", "Adım 4-5 — karar ve kuyruk",
"Adım 6 — defter". Adım numaraları `takimlar/x-icerik/takim.md` ile birebir aynıdır, yani
kaydı okuyan (insan ya da bekçi) hangi adımın atlandığını görebilir.

Örnekte okumaya değer üç ayrıntı:

- **Adım 1**, `--isle` boş dönmesine rağmen `gelen/` klasörünün elle listelendiğini yazıyor.
  Bu, kuralın gerçekten uygulandığının kanıtıdır — ve tam olarak
  [sorun giderme](../06-sorun-giderme.md)'deki ilk maddenin konusudur.
- **Adım 2-3**, `tweet_cek.py`'nin **neden çağrılmadığını** gerekçesiyle yazıyor. Yapılmayan
  iş de kayda girer; "yapmadım" değil, "şu sebeple yapmadım, şu dosyayı referans aldım".
- **Adım 4-5**, kuyruk maddelerinin neden `tamam` değil `bitti` yapıldığını söylüyor.
  Fark kritiktir: `tamam` zinciri tetikler ve `twitter-icerik`'e iş açar, `bitti` açmaz
  ([../02-dongu.md](../02-dongu.md)).

### Yetenek önerisi

Adım 6'nın içindeki kalın satır, bu kitin "kendini geliştiren ajan" mekanizmasının tam
gövdesidir:

```markdown
**Yetenek önerisi (insana):** `kaynak-dogrulama` → `## Öğrenilenler` bölümüne şu satır önerilir: …
Bu ders üç koşudur tekrar ediyor …; skill kendisi değiştirilmedi, karar patronun.
```

Üç şey birden yapıyor: dersi adlandırıyor, üç koşuda tekrarlandığını **kanıtlarıyla**
gösteriyor (hangi update_id'ler), ve yeteneği kendi değiştirmediğini açıkça yazıyor.
Mekanizmanın tamamı [../04-yetenekler.md](../04-yetenekler.md)'de.

Aynı bölümde "yeni ders eklenmedi" de yazıyor — gerekçesiyle. Ders yoksa deftere satır
eklenmez; doldurma yasaktır.

### `## Sonuç`

Sayılabilir kapanış. `takimlar/x-icerik/kurallar.md`'nin çıktı kalite ölçütü bunu ister:
*"Koşu kaydında kaç link, kaç tablo, kaç ⛔ ve dosya yolları var."* Örnekte beş satır:
kaç link, kaç yeni tablo, kaç yeni ⛔, üretilen/referans verilen dosya yolu, maliyet ve
kalan kuyruk.

Buradaki `~$0.32 USD` **ajanın kendi tahminidir**; makinenin saydığı gerçek rakam
altbilgidedir (`0.388 USD`). İkisinin farklı olması normaldir — bekçi ve raporlar
altbilgiyi okur.

"Kalan kuyruk" satırı ANAYASA §4'ün "ne kaldı" şartını karşılar: bir sonraki koşu bu satıra
bakarak başlar.

### `## Bekçi`

Bu bölümü **ajan yazmaz** — `bin/bekci.py` kaydın sonuna ekler (`_kaydet`). Üç satırdır:

```markdown
## Bekçi
- karar: **kabul**
- gerekçe: [bekçi aynı aileden — uyarı] …
- ihlal edilen kural: -
```

- `karar` — `kabul` · `red` · `atlandi`. **`atlandi` kabul değildir**, denetim yapılamadı demektir.
- `gerekçe` — bu örnekte ANAYASA maddelerini tek tek geziyor; iyi bir kabul gerekçesi böyledir.
- `ihlal edilen kural` — red'de dolar (`gizli veri`, `koşu kaydı`, kural numarası); kabulde `-`.

Baştaki `[bekçi aynı aileden — uyarı]` ibaresi, o gün `OPENAI_API_KEY` olmadığını ve yedek
Haiku yolunun kullanıldığını söyler. ANAYASA §3 bunu şart koşar: yedek yola düşülürse karar
işaretlenir, **sessizce geçilmez**. Ayrıntılar [../03-bekci.md](../03-bekci.md)'de.

`kos.py` bu başlığı arar (`_bekci_kosmus_mu`): varsa bekçi zaten koşmuş demektir, tekrar
çağrılmaz; yoksa sürücü denetimi kendisi başlatır. Yani denetimsiz koşu olmaz.

### Altbilgi

```markdown
---
- maliyet: 0.388 USD · tur: 19 · hata: False
```

Bunu da ajan değil sürücü yazar (`kos.kos()`), `claude -p --output-format json` çıktısından:

| Alan | Nereden | Ne demek |
|---|---|---|
| `maliyet` | `total_cost_usd` | Bu koşunun gerçek maliyeti. Tavan 2 USD (`takim.md` `butce_usd` ile değişebilir). |
| `tur` | `num_turns` | **İç döngünün** tur sayısı — ajanın kaç kez araç çağırıp yanıt ürettiği. |
| `hata` | `is_error` | Oturum hatayla mı bitti. `True` ise `son_sonuc: "hata"`. |

`tur: 19` bu kayıtta anlamlıdır: dışarıdan bakınca "tek prompt" görünen iş, içeride 19 turluk
bir döngüdür — dosya okuma, klasör listeleme, `durum.json` güncelleme, dosya taşıma.
Dış döngü / iç döngü ayrımı [../02-dongu.md](../02-dongu.md)'de.

Bu satırı iki yer okur: `dagitici.gunluk_maliyet` (günlük 10 USD tavanı için) ve
`gunluk.kosu_oku` (akşam raporu tablosu için). Biçimi bu yüzden sabittir.

---

## Koşu kaydı yazarken

- **Yapmadığın işi de yaz** — neden yapmadığın gerekçesiyle.
- **Dosya yolu ver.** "Çıktıyı yazdım" değil, hangi dosyaya.
- **Sayı ver:** kaç girdi, kaç çıktı, kaç etiket, kaç USD.
- **Ne kaldığını yaz.** Bir sonraki koşu oradan başlar.
- **Engel varsa `engel:` satırı** aç ve `durum.json` → `son_sonuc: "hata"` yap.
  *"Sessiz kalan koşu en kötü koşudur."* (`sirket/AJAN-KIMLIGI.md`)
- **Anahtar, e-posta, kişi adı yazma.** Bekçinin ön kontrolü bunları LLM'e sormadan red eder.
- Patronun notu anlaşılmıyorsa tahminle iş yapma: kayda `## Notlara cevap` başlığı altında
  soruyu sor, kuyruk maddesini `bekliyor` bırak.

---

## İlgili belgeler

- [../01-nasil-calisir.md](../01-nasil-calisir.md) — koşu kaydının sürücüdeki yeri
- [../02-dongu.md](../02-dongu.md) — bu koşuyu başlatan tetik
- [../03-bekci.md](../03-bekci.md) — `## Bekçi` bölümü nasıl oluşur
- [../04-yetenekler.md](../04-yetenekler.md) — "yetenek önerisi" satırının mekanizması
