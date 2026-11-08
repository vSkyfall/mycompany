# 05 · Kendi takımını açmak

Kitte üç takım var. Dördüncüsünü açmak dört dosya doldurmak demektir; kod yazmak gerekmez.
Bu belge sırayı ve `takim.md` frontmatter'ının tam anlamını verir.

Mimari [01-nasil-calisir.md](01-nasil-calisir.md)'de, yetenek bağı
[04-yetenekler.md](04-yetenekler.md)'de.

---

## 1 · İskeletten kopyala

```bash
bin/takim-olustur.sh linkedin-icerik
# kuruldu: takimlar/linkedin-icerik — şimdi takim.md'yi doldur
#          (akan şey, araçlar, koşu adımları, çıktı sözleşmesi)
```

Betik ne yapar:

- Adın **ASCII kebab-case** olduğunu doğrular (`^[a-z0-9]+(-[a-z0-9]+)*$`); değilse durur.
- `takimlar/<ad>` zaten varsa durur — üzerine yazmaz.
- `takimlar/_iskelet` klasörünü kopyalar, içine `kosu/` ve `cikti/` açar.
- Dört dosyadaki (`takim.md`, `kurallar.md`, `defter.md`, `durum.json`) `TAKIM` kelimesini
  takımın adıyla değiştirir.

Sonrasında elle doldurulacak dört dosya var. Hepsi [01-nasil-calisir.md](01-nasil-calisir.md)'de
tanımlı: `takim.md` = kim/ne, `kurallar.md` = sınır, `defter.md` = ders (boş başlar),
`durum.json` = kuyruk/durum (boş başlar).

---

## 2 · `takim.md` frontmatter — alanların tam listesi

```yaml
---
name: linkedin-icerik
description: LinkedIn içerik takımı olarak yayınlanmış X Article paketinden LinkedIn'e uygun
  tek bir uzun gönderi taslağı kurmak — yazmak, yayınlamak değil.
model: sonnet
tools: [Read, Write, Glob, Grep]
gerekli_anahtarlar: []
skills: [anlati-kurgusu, kaynak-dogrulama]
butce_usd: 2
---
```

| Alan | Kim okur | Anlamı |
|---|---|---|
| `name` | `agents_uret` | Takımın adı; klasör adıyla aynı olmalı. Agent frontmatter'ına aynen geçer. |
| `description` | `agents_uret`, `kos.py` | **Mesleğin.** İstemin ilk satırında `Mesleğin: …` diye görünür (`meslek_metni`). Boş bırakılırsa yerine `bu takımın işini yapmak.` yazılır — bırakma. |
| `model` | `kos.py` | `claude -p --model` değeri. Varsayılan `sonnet`. |
| `tools` | `kos.py` | `--allowedTools` listesi. Yoksa `Read, Write, Glob, Grep`. `Bash(python3 bin/tweet_cek.py *)` gibi dar kalıplar yazılabilir — **yazılmalı** da. |
| `gerekli_anahtarlar` | `kos.py` | Koşudan önce ortamda dolu olması gereken `.env` değişkenleri. Eksikse koşu `claude` çağrılmadan `atlandi` biter. |
| `skills` | `agents_uret`, `kos.py` | Yetenek listesi. Önsöze ve isteme `Yeteneklerin: …` satırı olarak girer. |
| `butce_usd` | `kos.py` | `--max-budget-usd` değeri. Yoksa `ayar.KOSU_BUTCESI_USD` = 2.0. |

Üç kritik ayrım:

- **`gerekli_anahtarlar`, `butce_usd` ve `skills` şirket alanlarıdır** (`SIRKET_ALANLARI`).
  `agents_uret` bunları agent frontmatter'ına **yazmaz**; sürücü ve önsöz kullanır.
- `name`, `description`, `model`, `tools` (`AGENT_ALANLARI`) agent frontmatter'ına aynen geçer.
- Bunların dışında yazdığınız **her alan da** agent frontmatter'ına geçer. Şirkete özel bir alan
  eklemek istiyorsanız `agents_uret.SIRKET_ALANLARI` setine de eklemeniz gerekir.

Frontmatter ayrıştırıcısı basittir (`ayar.frontmatter`): `anahtar: değer` ve `[a, b]` listeleri.
Değerler **metin olarak** okunur — `butce_usd: 2` ayrıştırıldığında `"2"` olur; `--max-budget-usd`
zaten metin beklediği için sorun çıkarmaz, ama kendi kodunuzda sayıya çevirmeyi unutmayın.
İç içe YAML, çok satırlı liste ve yorum satırı desteklenmez.

### Gövde

`_iskelet/takim.md`'nin bölümleri: `## Akan şey` (girdi/çıktı), `## Koşu adımları`,
`## Yetenekler`, `## Girdi kaynakları`, `## Çıktı sözleşmesi`. Mevcut üç takım buna bir de
`## Ne zaman koşarsın` ve `## Asla` bölümü eklemiş — ikisi de faydalıdır.

Koşu adımları **sırayla uygulanır** ve ajan adım dışına çıkmaz. İskeletin altı adımı her takımda
aynıdır ve son ikisi pazarlıksızdır:

```
5. `defter.md`'ye bu koşudan çıkan TEK dersi ekle (ders yoksa ekleme).
6. Koşu kaydını `SIRKET_KOSU` yoluna yaz: ne okudun, ne ürettin, ne kaldı, hangi kaynaklardan.
```

---

## 3 · `kurallar.md` — bekçinin okuduğu dosya

Bu dosya **bekçiye** yazılır: denetim isteminde `<kurallar>` bloğu olarak birebir geçer
([03-bekci.md](03-bekci.md)). Üç bölümü vardır:

- `## Neye göre çalışır` — hangi anayasa maddeleri ve hangi yetenek otoritedir.
- `## Asla yapmaz` — somut, kontrol edilebilir yasaklar. "Dikkatli olur" değil,
  "tarayıcıyla X'e girmez, gönderi atmaz, beğenmez, takip etmez".
- `## Çıktı kalite ölçütleri` — çıktının denetlenebilir nitelikleri.

Bekçinin istemi hedef aralıklardan %15'e kadar sapmayı red sebebi saymaz; o yüzden
"1.000–2.000 kelime" gibi aralıklar yazmak güvenlidir.

---

## 4 · Agent dosyasını üret ve kuru koş

```bash
python3 bin/agents_uret.py
# yazıldı: linkedin-icerik

python3 bin/kos.py linkedin-icerik --kuru
```

`--kuru` `claude`'u çağırmaz, hiçbir dosyaya yazmaz. Şunları basar:

```
kuru koşu — linkedin-icerik — 2026-09-13T21:40:00+02:00
  model: sonnet · bütçe: 2 USD · süre: 15 dk
  araçlar: Read, Write, Glob, Grep
  koşu kaydı yazılacak dosya: takimlar/linkedin-icerik/kosu/2026-09-13-2140.md
  gerekli anahtarlar: (yok)
  yetenekler: anlati-kurgusu, kaynak-dogrulama
  kimlik (istemin ilk satırı): Sen `linkedin-icerik` ajanısın. A Şirketi'nde bir çalışansın …
  istem (1843 karakter), ilk 400:
    …
  → claude çağrılmadı, hiçbir dosya yazılmadı.
```

Kontrol listesi: kimlik satırında meslek doğru mu, yetenek listesi beklediğiniz mi, araç listesi
fazla geniş değil mi, gerekli anahtarlar eksiksiz mi.

CI'da agent dosyasının `takim.md` ile uyumunu doğrulamak için:

```bash
python3 bin/agents_uret.py --check   # sapma varsa "SAPMA: linkedin-icerik" ve çıkış 1
```

### İsteğe bağlı: koşuya özel istem

`bin/prompt-<takim>.md` dosyası varsa içeriği koşu isteminin **sonuna** eklenir
(`kos.istem()`). Mevcut takımlarda bu dosya kısa tutulmuş (11–52 satır) ve o koşuya özgü
hatırlatmaları taşır — arama sayısı sınırı, tablo dili, kuyruk maddesini ne zaman `tamam`
yapacağı gibi. Kalıcı kurallar `takim.md` ve `kurallar.md`'ye yazılır; bu dosya zorunlu değildir.

---

## 5 · Dağıtıcı zincirine eklemek

Takım kendi başına iş bulmuyorsa (yani başka bir takımın çıktısını bekliyorsa) zincire
eklenmesi gerekir. Zincir tablosu `bin/dagitici.py` içinde, dosyanın başında, `ZINCIR` listesidir:

```python
ZINCIR = [
    {"ad": "x-yaziya-deger", "desen": re.compile(r"^x-(.+)$"), "takim": "twitter-icerik",
     "id": "aci-{0}", "not": "x-icerik kaynağı yazıya değer buldu; article açısını çıkar"},
]
```

Yeni bir halka eklemek — örneğin `twitter-icerik` paketini `tamam` yapınca `linkedin-icerik`
kuyruğuna iş düşsün:

```python
    {"ad": "article-linkedine", "desen": re.compile(r"^aci-(.+)$"), "takim": "linkedin-icerik",
     "id": "li-{0}", "not": "article paketi hazır; LinkedIn gönderi taslağını kur"},
```

| Alan | Anlamı |
|---|---|
| `ad` | Log ve raporlarda görünen halka adı. |
| `desen` | **Kaynak** takımın kuyruk id'sine uyan regex. Yakalama grupları `id` şablonuna geçer. |
| `takim` | **Hedef** takım — kuyruğuna madde düşecek olan. |
| `id` | Hedefte açılacak madde id'si; `{0}` birinci yakalama grubudur (slug'lanmış). |
| `not` | Maddenin `not` alanı — hedef ajan bunu okur. |

Kurallar: yalnızca `durum: "tamam"` maddeler zincire girer; hedef kuyrukta aynı id varsa
yeniden yazılmaz; ilk uyan zincir maddesi kazanır (liste sırası önemlidir).

Kuru denemek: `python3 bin/dagitici.py --kuru` — zincir satırlarını basar, kuyruğa yazmaz.

### Haftalık iş

Takım zincirden değil takvimden besleniyorsa `bin/gunluk.py` içindeki `HAFTALIK` listesine
madde eklenir:

```python
HAFTALIK = [{"takim": "youtube-analiz", "gun": 0, "id": "yt-{hafta}",
             "not": "haftalık kanal raporu — son 7 gün"}]
```

`gun` haftanın günüdür (0 = pazartesi), `{hafta}` ISO hafta kimliğidir (`YYYY-Www`).
Aynı haftanın maddesi ikinci kez yazılmaz.

---

## 6 · Yeni anahtar gerekiyorsa

Takım bir API kullanıyorsa anahtarı **iki yere** eklemek gerekir:

1. `takim.md` frontmatter'ında `gerekli_anahtarlar: [YENI_ANAHTAR]` — sürücü koşudan önce
   kontrol eder, eksikse `claude`'u hiç çağırmaz.
2. `.env.example` dosyasına, **değeri boş** ve üstünde nereden alınacağını söyleyen bir yorumla:

```bash
# Yeni servis (linkedin-icerik takımı bunu okur): servis.com → Settings → API keys
YENI_ANAHTAR=
```

Üç kural:

- `.env.example`'daki hiçbir değer dolu olamaz — `KANAL=@ornek-kanal` tek istisnadır
  (`test_env_orneginde_gercek_deger_yok`).
- `.env` `.gitignore`'dadır ve asla commit edilmez.
- Anahtar hiçbir çıktıya, koşu kaydına, deftere, loga yazılmaz. Bekçinin ön kontrolü
  koşu kaydında anahtar deseni görürse LLM'e sormadan **red** verir ([03-bekci.md](03-bekci.md)).

---

## 7 · Testleri koştur

```bash
python3 -m unittest discover -s tests
```

Yeni takım için kırılabilecek testler:

- `test_gercek_takimlarin_frontmatteri_okunur` — `name` ve `tools` okunabiliyor mu.
- `test_her_takim_en_az_bir_skill_bildirir` — `skills:` alanı boş olamaz.
- `test_bildirilen_her_skill_diskte_var` — yazdığınız yetenek adı `skills/` altında var mı.
- `test_skill_takimlar_alani_takim_md_ile_tutarli` — `SKILL.md`'nin `takimlar:` listesine
  yeni takımı da eklediniz mi (**çift yönlü bağ**).
- `test_govdede_yetenekler_bolumu_var` — gövdede `## Yetenekler` başlığı.
- `test_env_ornegi_ile_readme_ayni_anahtarlari_sayiyor` — `.env.example`'a eklediğiniz her
  anahtar `README.md`'de de geçmeli.

---

## Örnek: `linkedin-icerik` takım.md taslağı

Aşağıdaki **varsayımsal** bir örnektir; kitte böyle bir takım yoktur. Yapıyı göstermek içindir.

```markdown
---
name: linkedin-icerik
description: LinkedIn içerik takımı olarak twitter-icerik'in hazırladığı X Article paketinden
  LinkedIn'e uygun tek bir uzun gönderi taslağı kurmak — taslağa kadar, yayınlamak değil.
model: sonnet
tools: [Read, Write, Glob, Grep]
gerekli_anahtarlar: []
skills: [anlati-kurgusu, kaynak-dogrulama]
butce_usd: 2
---

# linkedin-icerik

## Ne zaman koşarsın
- **Zincir (asıl yol):** `twitter-icerik` bir `aci-` maddesini `tamam` yaptığında dağıtıcı
  kuyruğuna `li-<id>` düşürür.
- **Sabah 09:00:** kuyrukta bekleyen `li-` maddesi varsa sıra sende.
- **Elle:** `python3 bin/kos.py linkedin-icerik`.

Mesai 09:00–23:00 dışında koşmazsın. Günde en fazla bir gönderi taslağı.

## Akan şey
Girdi: `durum.json` kuyruğundaki `li-<id>` maddesi ve arkasındaki paket
(`takimlar/twitter-icerik/cikti/<tarih>-<slug>/article.md`, salt okunur).
Çıktı: `takimlar/linkedin-icerik/cikti/YYYY-MM-DD-<slug>.md`

## Koşu adımları
1. Kuyruktaki `li-<id>` maddesini ve dayandığı article paketini oku.
2. `skills/anlati-kurgusu` ile tek beatlik açılışı kur; gövdeyi 200–400 kelimeye indir.
3. `skills/kaynak-dogrulama` ölçüsüyle etiketleri taşı — **⛔ iddia gönderiye girmez.**
4. Çıktıyı `cikti/` altına yaz; kuyruk maddesini `tamam` yap, `not` alanına dosya yolunu koy.
5. `defter.md`'ye en fazla bir ders (ders yoksa ekleme).
6. Koşu kaydını `SIRKET_KOSU` yoluna yaz: kelime sayısı, dosya yolu, maliyet.

## Yetenekler
Adım 2-3'te okunur:
- `skills/anlati-kurgusu/SKILL.md` — açılış ve yay
- `skills/kaynak-dogrulama/SKILL.md` — etiketleri yazıya taşırken ölçü

## Girdi kaynakları
- `durum.json` kuyruğu — `li-<id>` maddeleri (dağıtıcı taşır); `not-` maddeleri patronundur
- `takimlar/twitter-icerik/cikti/*/article.md` — salt okunur

## Çıktı sözleşmesi
`cikti/YYYY-MM-DD-<slug>.md`
- 200–400 kelime, tek gönderi, tablo yok, kişi adı yok
- her iddia etiketli (✅/🟡) ve kaynaklı

## Asla
- LinkedIn'e yazma, yayınlama, zamanlama — yayın düğmesi insanda (ANAYASA §1)
- ⛔ etiketli iddiayı gönderiye alma; kaynaksız sayı yazma
- Başka takımın klasörüne yazma; `twitter-icerik` çıktısı salt okunur
```

Bu taslak çalışır hâle gelmesi için gereken kalan iki şey: `kurallar.md`'nin doldurulması ve
`bin/dagitici.py` → `ZINCIR` listesine `article-linkedine` halkasının eklenmesi.

---

## Sırada

- Bir şey çalışmıyorsa: [06-sorun-giderme.md](06-sorun-giderme.md)
- Yetenek eklemek: [04-yetenekler.md](04-yetenekler.md)
