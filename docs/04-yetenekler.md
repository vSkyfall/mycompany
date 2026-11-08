# 04 · Yetenekler (skills)

Bir yetenek, **bir işin nasıl yapılacağını** adım adım, şablonuyla ve kontrol listesiyle anlatan
tek dosyadır: `skills/<ad>/SKILL.md`. Ajan koşu adımında yalnızca ilgili yeteneği okur.

Kitte sekiz yetenek, üç takım var. Kataloğun kendisi `sirket/YETENEKLER.md`'dedir; bu belge
mekanizmayı anlatır.

---

## Neden ayrı dosya — üç gerekçe

`sirket/YETENEKLER.md` ve `sirket/AJAN-KIMLIGI.md` aynı üç gerekçeyi sayar:

1. **Token sorununu çözmek.** Bir işin nasıl yapılacağını her koşuda baştan anlatmak pahalıdır
   ve her seferinde biraz farklı çıkar. Yetenek dosyası bir kez yazılır, ajan koşuda sadece
   ilgili adımda okur.
2. **Hatırlamak.** Ajanın hafızası yok; oturum kapanınca her şey gider. `defter.md` **dünü**,
   `skills/` ise **nasıl yapıldığını** hatırlar. Yazmadığın şey olmamıştır.
3. **Gelişmek.** Her yetenek dosyasının sonunda `## Öğrenilenler` bölümü var. Ajan koşuda
   aldığı veriyle kendini geliştirir: dersi `defter.md`'ye yazar, aynı ders üç koşuda tekrar
   ederse yeteneğin `## Öğrenilenler` bölümüne öneri bırakır. Kararı insan verir.
   Pazartesi öğrenilen, salı davranışa döner.

---

## `SKILL.md` yapısı

### Frontmatter (zorunlu)

```yaml
---
name: kaynak-dogrulama
description: Bir X yazısı, makale ya da video transkriptindeki iddiaları tek tek birincil
  kaynağa kadar açıp ✅/🟡/⛔ ile sınıflar; … X içerik ve twitter içerik takımları kullanır.
kaynak: A Şirketi kitinin kendi üretimi — dış kaynak yok
lisans: —
uyarlayan: A Şirketi (2026-09-11)
takimlar: [x-icerik, twitter-icerik]
---
```

| Alan | Ne yazar |
|---|---|
| `name` | Yeteneğin adı. **Klasör adıyla birebir aynı olmalı**, ASCII kebab-case. |
| `description` | Ne yaptığı ve **hangi takımın ne zaman okuduğu**. Tek paragraf. |
| `kaynak` | Dışarıdan alındıysa tam URL + commit + tarih; kendi üretimimizse öyle yazar. |
| `lisans` | Alınan deponun lisansı (hepsi MIT) ya da `—`. |
| `uyarlayan` | Kim uyarladı, ne zaman. |
| `takimlar` | Bu yeteneği bildiren takımların listesi — `takim.md` ile **çift yönlü** tutarlı olmalı. |

Bu altı alan `tests/test_skills.py` içindeki `ZORUNLU_ALANLAR` listesidir; biri eksikse test kırılır.

### Gövde

Kitteki yeteneklerin ortak iskeleti:

- **Tek cümlelik tez** — dosyanın ilk satırı, kalın. ("Hedefe eşlenmeyen sayı KPI değil,
  teşhistir.")
- `## Ne zaman` — bu yetenek hangi durumda okunur.
- `## Pazarlıksız kural(lar)` ya da `## Üç ilke` — tartışılmayacak sınırlar.
- `## Çerçeve: <KISALTMA>` — işin akılda kalan omurgası (ÖLÇ, YAY, DENET, SIFT).
- `## Adımlar` — sırayla ne yapılır.
- `## Çıktı şablonu` — birebir kopyalanacak biçim.
- `## Kalite kontrol listesi` — bitirmeden önce.
- `## Yasaklar (ANAYASA)` — bu işte hangi anayasa maddesi nasıl uygulanır.
- `## Öğrenilenler` — **zorunlu**, aşağıda.
- `## Kaynak ve değişiklikler` — **dışarıdan alınan her yetenekte zorunlu**;
  `Orijinalden alınanlar` ve `Değiştirilenler` alt başlıklarını taşır.

Dosya **250 satırı geçemez** (`test_skill_uzunlugu_sinirda`). Yetenek bir el kitabı değil,
bir kontrol listesidir; uzarsa okunmaz ve token yer.

---

## `takim.md` ile bağ

Bağ tek yerde kurulur: `takimlar/<takim>/takim.md` frontmatter'ındaki `skills:` alanı.

```yaml
skills: [kaynak-dogrulama, iddia-ayristirma-ve-kanit-defteri, kaynak-kimlik-dogrulama]
```

Oradan iki yol çıkar:

1. **`bin/agents_uret.py`** bu alanı *şirket alanı* sayar (`SIRKET_ALANLARI`) — agent
   frontmatter'ına sızmaz — ve `.claude/agents/<takim>.md` önsözüne tek satır ekler:

   > `Yeteneklerin: \`skills/kaynak-dogrulama/SKILL.md\`, \`skills/iddia-ayristirma-ve-kanit-defteri/SKILL.md\`, \`skills/kaynak-kimlik-dogrulama/SKILL.md\` — ilgili adımda oku ve uygula.`

2. **`bin/kos.py`'nin `istem()` fonksiyonu** aynı satırı koşu istemine koyar
   (`agents_uret.yetenek_satiri`). Yani ajan hem agent dosyasında hem istemde aynı listeyi görür.

Göstermek için:

```bash
python3 bin/kos.py x-icerik --kuru
#   yetenekler: kaynak-dogrulama, iddia-ayristirma-ve-kanit-defteri, kaynak-kimlik-dogrulama
```

### "Sadece ilgili adımda okunur"

Yetenek satırı listeyi verir ama **okumayı emretmez**; "ilgili adımda oku ve uygula" der.
Hangi adımda hangi yeteneğin okunacağı `takim.md`'nin `## Yetenekler` bölümünde yazar:

```markdown
## Yetenekler
Adım 3'te okunur:
- `skills/iddia-ayristirma-ve-kanit-defteri/SKILL.md` — metni tek tek iddialara bölmek
- `skills/kaynak-dogrulama/SKILL.md` — etiketleme ve tablo şablonu (format otoritesi)
- `skills/kaynak-kimlik-dogrulama/SKILL.md` — yalnız kaynağın kim olduğundan şüphe varsa
```

Bunun sebebi token: üç yetenek dosyası koşunun başında toptan okunursa her koşu birkaç yüz satır
fazladan bağlam taşır ve çoğu o koşuda kullanılmaz. `kaynak-kimlik-dogrulama` iyi bir örnektir —
yalnızca **kaynağın kim olduğundan şüphe varsa** açılır, her koşuda değil.

### Bütünlük testleri

`tests/test_skills.py` bağı çift yönlü denetler:

- Bildirilen her yetenek diskte var mı (`skills/<ad>/SKILL.md`).
- `SKILL.md`'nin `takimlar:` listesinde geçen her takım, kendi `takim.md`'sinde o yeteneği
  bildiriyor mu. (Tek yönlü bildirim testi kırar.)
- Her `SKILL.md` `## Öğrenilenler`, "kendini geliştir" ve `defter.md` geçiyor mu.
- Dışarıdan alınan her yetenek `## Kaynak ve değişiklikler` + `Orijinalden alınanlar` +
  `Değiştirilenler` taşıyor mu.
- `sirket/YETENEKLER.md` kataloğu her yeteneği ve her kaynak URL'ini listeliyor mu.
- Her takım en az bir yetenek bildiriyor mu; `_iskelet` boş `skills: []` taşıyor mu.

---

## `## Öğrenilenler` — ajanın kendini geliştirme mekanizması

Bu kitteki "kendini geliştiren ajan" iddiasının tamamı üç adımlık bu çarktır:

```
    koşu → ders                 ders üç kez tekrar         insan kararı
  ┌───────────────┐          ┌────────────────────┐     ┌────────────────────┐
  │ defter.md'ye  │  ──────► │ koşu kaydına       │ ──► │ SKILL.md           │
  │ EN FAZLA      │          │ "yetenek önerisi:  │     │ ## Öğrenilenler    │
  │ BİR ders      │          │  <yetenek> → …"    │     │ bölümüne işlenir   │
  └───────────────┘          └────────────────────┘     └────────────────────┘
       ajan yazar                   ajan yazar               İNSAN yazar
```

1. **Ders `defter.md`'ye.** Her koşudan en fazla bir ders, yeni ders üste. Ders yoksa
   eklenmez — "bu koşuda da öğrendim" doldurması yasaktır.
2. **Tekrar ederse koşu kaydına öneri.** Aynı ders üç koşuda tekrar ediyorsa ajan koşu kaydına
   şu satırı bırakır: `yetenek önerisi: <yetenek adı> → ## Öğrenilenler'e şu satır eklensin: …`
3. **Kararı insan verir.** Ajan `SKILL.md`'yi **kendi değiştirmez**. Her yetenek dosyasında bu
   yazılıdır: *"skill'i kendi başına değiştirme"*. Aynı kural `kurallar.md` ve `ANAYASA.md` için
   de geçerlidir (ANAYASA §5: defter ajanın, kural insanın).

Gerçek bir örnek — 11 Eylül koşusundan, adım 6:

```markdown
**Yetenek önerisi (insana):** `kaynak-dogrulama` → `## Öğrenilenler` bölümüne şu satır önerilir:
"Aynı link ardışık koşularda tekrar düşerse `tweet_cek.py` yeniden çağrılmaz; önceki çıktı
dosyasına referansla kuyruk maddesi 'yinelenen mesaj' notuyla kapatılır." Bu ders üç koşudur
tekrar ediyor …; skill kendisi değiştirilmedi, karar patronun.
```

Tam kayıt: [ornek-kosu/kosu-kaydi.md](ornek-kosu/kosu-kaydi.md).

Neden insan araya giriyor: ajanın üç koşuda gördüğü bir desen kalıcı bir kural olmayabilir
(o hafta aynı link beş kez düştüğü için doğru görünen bir kısayol, başka bir hafta yanlış olur).
Defter ucuzdur ve geri alınabilir; yetenek dosyası o işin **otoritesidir** ve her koşuyu etkiler.

---

## Sekiz yetenek — hangi takım, hangi adım

| Yetenek | Takım | Hangi adımda | Ne işe yarar | Kaynak · lisans |
|---|---|---|---|---|
| `iddia-ayristirma-ve-kanit-defteri` | `x-icerik` | Adım 3 — tablodan **önce** | Metni kontrol edilebilir iddialara böler, her iddiaya izi sürülebilir kanıt satırı koyar; "kanıt yok" ile "çelişen kanıt var"ı ayırır | petar-nauka/fact-check-skill · MIT |
| `kaynak-dogrulama` | `x-icerik` | Adım 3 — tabloyu yazarken | Rozet tanımları (✅ birincil · 🟡 ikincil · ⛔ doğrulanamadı) ve `\| İddia \| Durum \| Ne söylenir \|` şablonu; **format otoritesi** | kendi üretimimiz · — |
| `kaynak-kimlik-dogrulama` | `x-icerik` | Adım 3 — **yalnız şüphe varsa** | SIFT ile kaynağın kim olduğunu, materyalin gerçekliğini ve iddiayı desteklediğini ayrı ayrı sınar; metin çekilemediğinde ya da ekran görüntüsü geldiğinde | jamditis/claude-skills-journalism · MIT |
| `analitik-okuma-ve-raporlama` | `youtube-analiz` | Adım 2 — raporu yazarken | Ham izleyici verisini hedefe bağlı rapora çevirir; **her sayının yanında** `[veri/YYYY-Www.json]` etiketi, üç öneriyle biter | social-media-skills/skills · MIT |
| `icerik-denetimi` | `youtube-analiz` | Adım 3 — "ne işe yaradı" | Son ~90 günün içeriğini tut / bırak / tazele diye triyaj eder, tutulmayan sözleri bulur | social-media-skills/skills · MIT |
| `anlati-kurgusu` | `twitter-icerik` | Adım 2 — omurgayı kurarken | Gerçek hikâyeyi bulur ve üç beatlik yaya oturtur (kurulum → dönüm → ödül); **hikâye uydurmayı yasaklar** | social-media-skills/skills · MIT |
| `x-article-format` | `twitter-icerik` | Adım 2 — `article.md`'yi yazarken | Uzunluk (1.000–2.000 kelime), iskelet (3–7 bölüm), **tablo yasağı**, görsel yeri, kontrol listesi; **format otoritesi** | kendi üretimimiz · — |
| `zincir-yazimi` | `twitter-icerik` | Adım 2 — lansman postu / zincir | X zinciri ve lansman postunu yazar; "bu aslında tek post olmalı" itirazını söyleme izni vardır | social-media-skills/skills · MIT |

`kaynak-dogrulama` **iki takımda** bildirilidir: `x-icerik` tabloyu üretirken, `twitter-icerik`
tablodaki etiketleri yazıya taşırken ölçü olarak kullanır.

### Nereden alındı

| Depo | Ne | Lisans | Kaç yetenek |
|---|---|---|---|
| social-media-skills/skills | Sosyal medya skill'leri (yazım, analitik, denetim) | MIT | 4 |
| petar-nauka/fact-check-skill | Fact-checking ve kanıt defteri | MIT | 1 |
| jamditis/claude-skills-journalism | Gazetecilik: doğrulama ve kaynak | MIT | 1 |

`kaynak-dogrulama` ve `x-article-format` kitin kendi üretimidir; dış kaynağı yoktur.
Tam liste ve URL'ler `sirket/YETENEKLER.md`'de.

### Uyarlamada ne değişti

Dışarıdan alınan her dosyanın sonundaki `## Kaynak ve değişiklikler` bölümü bunu yazar.
Değişikliklerin ortak yönü:

- **ANAYASA §1** gereği yayınlama / mail / zamanlama / para adımları çıkarıldı — hepsi insanda.
- **ANAYASA §2** gereği kaynağı açılmamış üçüncü taraf sayıları çıkarıldı; ✅/🟡/⛔ etiketleme
  eklendi; kişisel veri (kullanıcı adı, e-posta) yasağı eklendi.
- **ANAYASA §5** gereği takımlar arası mesajlaşma çıkarıldı; çıktı dosyaya yazılır, okuyan okur.
- Dış araç zincirleri çıkarıldı; girdi/çıktı yolları bu reponun dosya sözleşmesine bağlandı.

---

## Yetenek eklerken

1. `skills/<ad>/SKILL.md` aç — ad ASCII kebab-case, frontmatter'da altı zorunlu alan,
   gövdede `## Öğrenilenler`, dosya 250 satırı geçmesin.
2. İlgili `takimlar/<takim>/takim.md` frontmatter'ına `skills:` listesine adı ekle.
3. `SKILL.md`'nin `takimlar:` alanına o takımı ekle — **çift yönlü**, yoksa test kırılır.
4. `takim.md`'nin `## Yetenekler` bölümüne "hangi adımda okunur" satırını yaz.
5. `sirket/YETENEKLER.md` kataloğunu güncelle (ad + varsa kaynak URL'i).
6. `python3 bin/agents_uret.py` ve `python3 -m unittest discover -s tests`.

Adım adım yeni takım açmak: [05-yeni-takim.md](05-yeni-takim.md).

---

## Sırada

- Kendi takımını açmak: [05-yeni-takim.md](05-yeni-takim.md)
- Mimari: [01-nasil-calisir.md](01-nasil-calisir.md)
