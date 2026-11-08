# 03 · Bekçi — ayrı kafa

> **ANAYASA §3:** Üreten Claude ise denetleyen başka model ailesinden olur; üreten kendi işini
> onaylayamaz. Bekçi Stop hook'ta, ayrı süreçte çalışır (`bin/bekci.py`); kararı koşu kaydının
> altına ve `durum.json`'a düşer.

Bekçi bu kitteki en küçük ama en belirleyici parçadır: ajanın çıktısının patronun önüne gidip
gitmeyeceğine o karar verir. LLM'e "iyi davran" demekle yetinmez, **çıkışta** durur.

Döngüdeki yeri [02-dongu.md](02-dongu.md)'de, sürücüyle ilişkisi
[01-nasil-calisir.md](01-nasil-calisir.md)'de.

---

## Neden ayrı aile

Aynı model ailesi kendi hatasını **aynı sebeple** onaylar: üreten hangi gerekçeyle
"bu yeterince kaynaklı" dediyse, denetleyen de aynı gerekçeyle onaylar. Hata bağımsız değildir.

Bu yüzden kit şunu ister: üreten Claude ise denetleyen OpenAI olsun. Anahtar yoksa iş durmaz ama
**sessizce geçilmez** — yedek yola düşülür ve karar dürüstçe işaretlenir:

```
[bekçi aynı aileden — uyarı] Koşu kaydı ANAYASA'nın tüm maddelerine uygun: …
```

Bu ibare `bekci.AYNI_AILE_UYARISI` sabitinden gelir ve gerekçenin **başına** eklenir.
Akşam raporunda, `durum.json`'da ve telemetri dosyasında aynen görünür.

---

## Stop hook mekaniği

Tek hook vardır, `.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR\"/bin/bekci.py",
            "timeout": 180 }
        ]
      }
    ]
  }
}
```

Ajan oturumu bitirmek üzereyken Claude Code bu komutu çalıştırır ve **stdin'e bir JSON** verir.
`bekci.py` o JSON'dan tek bir alanı okur: `stop_hook_active`.

Takım ve koşu dosyası stdin'den değil **ortamdan** gelir:

- `SIRKET_TAKIM` — hangi takım koşuyor
- `SIRKET_KOSU` — koşu kaydının tam yolu

Bu ikisini `kos.py` alt sürece koyar. `SIRKET_TAKIM` yoksa bekçi hemen 0 döner ve karışmaz —
yani repoda elle `claude` açtığınızda hook ateşlense bile bir şey yapmaz. `SIRKET_KOSU` yoksa
takımın `kosu/` klasöründeki en son `.md` dosyası kullanılır.

Karar `red` ise hook stdout'a şunu basar:

```json
{"decision": "block",
 "reason": "🛑 BEKÇİ RED: <gerekçe>\nKoşu kaydını (<yol>) düzelt, sonra bitir."}
```

`decision: "block"` Claude Code'a "bu oturumu bitirme" der; ajan **aynı oturumda** düzeltmeye
döner, gerekçeyi okur, kaydı toparlar ve yeniden bitirmeye çalışır. Kabul edilen kararda hook
hiçbir şey basmaz, sessizce geçer.

### En fazla 2 red

Sonsuz döngü riski iki ayrı mekanizmayla kapatılır.

1. **Deneme sayacı.** `takimlar/<takim>/kosu/.bekci-deneme` dosyasında red sayısı tutulur.
   `MAKS_RED = 2`; sayaç 2'ye ulaştığında `engelle_mi()` artık `False` döner — bekçi kararını
   yine kaydeder ama ajanı bir daha geri göndermez. Kabul geldiğinde sayaç silinir.
2. **`stop_hook_active`.** Claude Code ikinci kez durdurulan bir oturumda bu bayrağı `true`
   gönderir. Bekçi o durumda engellemez, ama **son kararı yeniden verir** ve kaydeder — sayaç
   temizlenir. Yani son hâli her zaman denetlenmiş olur.

`bekci.py` her yolda **çıkış kodu 0** döner. Sözleşme nettir: bekçi oturumu düşürmez.
Anahtar yoksa, ağ yoksa, yanıt bozuksa karar `atlandi`dır — **`kabul` değil.**

---

## İki katman

### Katman 1 — ön kontrol (LLM yok)

Koşu kaydı önce regex süzgecinden geçer. Eşleşme varsa karar **doğrudan `red`**, LLM hiç
çağrılmaz — bu katman anahtarsız da çalışır ve para harcamaz.

| Ad | Desen |
|---|---|
| e-posta adresi | `[\w.+-]+@[\w-]+\.[\w.-]+` |
| OpenAI anahtarı | `\bsk-[A-Za-z0-9_-]{6,}` |
| Google anahtarı | `\bAIza[0-9A-Za-z_-]{6,}` |
| GitHub token | `\bgh[pousr]_[A-Za-z0-9]{6,}` |
| Telegram bot token | `\b\d{8,}:[A-Za-z0-9_-]{20,}` |
| fal anahtarı | `\b[0-9a-f-]{20,}:[0-9a-f]{16,}` |

Gerekçe: `ön kontrol: OpenAI anahtarı koşu kaydında geçiyor`, ihlal edilen kural: `gizli veri`.

Ayrıca kayıt **boşsa** (yalnızca boşluk) LLM'e hiç gidilmez:
`koşu kaydı boş — ajan SIRKET_KOSU dosyasını yazmadı`, ihlal: `koşu kaydı`.
ANAYASA §4'ün "kayıtsız koşu reddedilir" maddesi burada uygulanır.

### Katman 2 — LLM denetimi

Ön kontrol temizse istem kurulur. İçinde üç blok vardır — hepsi **görünür sınırlar** içinde:

```
<anayasa>  ANAYASA.md'nin tamamı            </anayasa>
<kurallar> takimlar/<takim>/kurallar.md     </kurallar>
<kosu>     koşu kaydı, ilk 24.000 karakter  </kosu>
```

Denetçiye verilen yönerge özetle: *"Sen bir içerik şirketinin bağımsız denetçisisin. Üretici
başka bir modeldir. Kanıt olmadan 'kabul' verme; şüphede 'red'. Yalnızca JSON döndür."*

İstemde üç ek sınır var, üçü de yanlış red'i önlemek için:

- **Madde 3 ve 4 denetçinin konusu değildir.** Onlar sürücünün kuralıdır (ayrı kafa, tavanlar);
  koşu kaydı bunlardan söz etmiyor diye red verilmez. Denetlenecek olan kaydın **içeriğidir**.
- **"Kaynaksız sayı" yalnızca dış dünya iddiaları içindir** — görüntülenme, abone, fiyat, gelir,
  tarih. Koşu altbilgisi (maliyet/tur/hata), kelime ve dosya sayıları, saatler ve kaydın kendi
  ölçümleri kaynak istemez.
- **Kural dosyasındaki hedef aralıklardan %15'e kadar sapma red sebebi değildir**; gerekçeye
  🟡 not düşülür, karar `kabul` verilir.

**Yol A — OpenAI.** `OPENAI_API_KEY` varsa `https://api.openai.com/v1/responses` çağrılır;
model `BEKCI_MODEL` ortam değişkeninden, yoksa `gpt-5-mini`. Yanıt `json_schema` ile
şemaya bağlanır (`strict: true`):

```json
{ "karar": "kabul | red", "gerekce": "…", "ihlal_edilen_kural": "… | null" }
```

Zaman aşımı 60 sn. Ağ hatası, bozuk JSON ya da şemaya uymayan yanıt → `atlandi`
(`bekçi ulaşılamadı: URLError`, `bekçi yanıtı çözümlenemedi`).

**Yol B — yedek Haiku.** Anahtar yoksa aynı istem `claude -p --model haiku` ile ayrı bir
süreçte, ayrı bir pencerede sorulur: `--max-budget-usd 0.2`, `--allowedTools ""` (araç yok),
timeout 150 sn. Ortamdan `CLAUDECODE`, `SIRKET_TAKIM` ve `SIRKET_KOSU` **silinir** — bekçi
kendini koşu sanmasın diye. Dönen metinden ilk `{` ile son `}` arası ayıklanır; JSON yoksa
`atlandi`. Karar geldiğinde gerekçenin başına `[bekçi aynı aileden — uyarı]` eklenir.

### Geçersiz red'in ayıklanması

`gecersiz_gerekceyi_ayikla()` bir emniyet supabıdır: gerekçesinde `madde 3`, `madde 4`,
`§3`, `§4`, `ayrı kafa`, `aynı aile` ya da `tavan` geçen — ya da `ihlal_edilen_kural` alanı
`"3"` / `"4"` olan — red'ler **geçersiz sayılır** ve `kabul`a çevrilir, not düşülerek:

```
(madde 3/4 gerekçeli red geçersiz sayıldı — sürücünün kuralı) …
```

Sebep: denetçi sık sık "bu kaydı aynı aileden bir model denetlemiş, madde 3 ihlali" ya da
"kayıtta tavan yazmıyor" diyerek içerikten bağımsız red veriyor. O maddeler ajanın değil
sürücünün sorumluluğudur. **İçerik gerekçeli red'lere dokunulmaz** — kaynaksız sayı, kişi adı,
anahtar sızıntısı red olarak kalır.

---

## `--dogrudan` modu

Hook dışından bir koşuyu denetlemek için:

```bash
python3 bin/bekci.py --dogrudan x-icerik
python3 bin/bekci.py --dogrudan x-icerik takimlar/x-icerik/kosu/2026-09-11-1716.md
```

Dosya verilmezse takımın en son koşu kaydı alınır. Karar JSON olarak stdout'a basılır ve
**normal yoldaki gibi kaydedilir** (koşu kaydı + `durum.json` + telemetri). Koşu kaydı yoksa
`{"karar": "atlandi", "gerekce": "koşu dosyası yok"}`.

`kos.py` de bu fonksiyonu kullanır: Stop hook herhangi bir sebeple koşmamışsa (kayıtta
`## Bekçi` başlığı yoksa) sürücü `bekci.denetle()`'yi doğrudan çağırır. Yani **denetimsiz koşu
olmaz.**

---

## Karar nereye yazılır

Her karar üç yere birden düşer (`_kaydet`):

**1 · Koşu kaydının altına**, `---` altbilgisinden önce:

```markdown
## Bekçi
- karar: **kabul**
- gerekçe: [bekçi aynı aileden — uyarı] Koşu kaydı ANAYASA'nın tüm maddelerine uygun: …
- ihlal edilen kural: -
```

**2 · `durum.json` → `bekci`:**

```json
"bekci": {
  "son_karar": "kabul",
  "red_sayisi_7g": 0,
  "gerekce": "[bekçi aynı aileden — uyarı] …",
  "zaman": "2026-09-11T17:19:20+02:00"
}
```

`red_sayisi_7g` her red'de bir artar. Bir sonraki koşuda ajan bu alanı okur: red gelmişse
önce gerekçeyi okuyup ona göre başlar.

**3 · `takimlar/bekci-telemetri.jsonl`** — append-only, satır başına bir karar:

```json
{"zaman":"…","takim":"x-icerik","kosu":"2026-09-11-1716.md","karar":"kabul","gerekce":"…","ihlal_edilen_kural":null}
```

Akşam raporu bu dosyayı okur: gün içindeki kabul / red / atlandı sayıları ve karar tablosu
oradan gelir. `*.jsonl` `.gitignore`'dadır.

---

## Örnek: gerçek bir kabul kararı

Aşağıdaki `x-icerik`'in 11 Eylül 17:16 koşusundan, olduğu gibi
([ornek-kosu/kosu-kaydi.md](ornek-kosu/kosu-kaydi.md)'deki tam kayıt):

```markdown
## Bekçi
- karar: **kabul**
- gerekçe: [bekçi aynı aileden — uyarı] Koşu kaydı ANAYASA'nın tüm maddelerine uygun:
  (1) sosyal ağa yazma/mesaj gönderme/yorum yok; (2) kaynaksız dış dünya iddiası yok
  (maliyet/ölçümler koşu altbilgisi); (3) denetçi atanmış; (4) mesai içinde (17:16),
  maliyet $0.32 USD tavanda; (5) defter ve kurallar insana bırakılmış, yetenek önerisi
  belirtilmiş. Kurallar dosyasında yasaklanmış işlem yok. Yinelenen mesaj durumu tutarlı
  belgelenmiş (referans dosya verilmiş, kuyruk maddesi durum.json'a kaydedilmiş).
  Dosyalar gelen/islendi/ altına taşınmış. Koşu kaydı tam ve denetlenebilir.
- ihlal edilen kural: -
```

Okunacak üç şey var. Birincisi, `[bekçi aynı aileden — uyarı]` — o gün `OPENAI_API_KEY` yoktu,
yedek Haiku yolu kullanıldı ve karar dürüstçe işaretlendi. İkincisi, gerekçe ANAYASA
maddelerini tek tek geziyor: bu iyi bir kabul gerekçesidir, "her şey yolunda" değil.
Üçüncüsü, gerekçe kaydın **içeriğinden** konuşuyor (hangi dosya taşındı, hangi madde nereye
yazıldı) — denetlenebilir olmanın anlamı budur.

## Örnek: red nasıl görünür

Ön kontrole takılan bir kayıt (kayıtta `sk-` ile başlayan bir dizge geçtiği için):

```markdown
## Bekçi
- karar: **red**
- gerekçe: ön kontrol: OpenAI anahtarı koşu kaydında geçiyor
- ihlal edilen kural: gizli veri
```

Bu kararda LLM hiç çağrılmadı, para harcanmadı. Hook stdout'a `decision: block` bastı, ajan
aynı oturumda kaydı düzeltip yeniden bitirmeye gitti. İkinci red'de (`MAKS_RED = 2`) oturum
kapanır, `son_sonuc: "red"` yazılır ve iş bir sonraki koşuya kalır.

Boş kayıt red'i de aynı biçimde görünür:
`koşu kaydı boş — ajan SIRKET_KOSU dosyasını yazmadı`, ihlal: `koşu kaydı`.

---

## Bekçiyi ikna etmek yok

`sirket/AJAN-KIMLIGI.md`'deki cümle açıktır: *"Bekçiyi ikna etmeye çalışma; kaynaklı yaz."*
Red gelince doğru hamle gerekçeyi tartışmak değil, eksik kaynağı koymak ya da kaynaksız cümleyi
kaldırmaktır. Bekçinin göremediği tek şey, kayda yazılmamış olan şeydir — bu yüzden
**kayıt ajanın savunmasıdır.**

---

## Sırada

- Yetenekler: [04-yetenekler.md](04-yetenekler.md)
- Bekçi "atlandi" diyorsa: [06-sorun-giderme.md](06-sorun-giderme.md)
