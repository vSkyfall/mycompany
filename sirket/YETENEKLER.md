# YETENEKLER — A Şirketi

> Üç takımın kullandığı sekiz yeteneğin kataloğu.
> Bir yetenek, o işin nasıl yapılacağını adım adım, şablonuyla ve kontrol listesiyle anlatan tek dosyadır:
> `skills/<ad>/SKILL.md`. Ajan koşu adımında **yalnızca ilgili yeteneği** okur.

## Neden bu dosyalar var — üç gerekçe

1. **Token sorununu çözmek.** Bir işin nasıl yapılacağını her koşuda baştan anlatmak pahalıdır ve her
   seferinde biraz farklı çıkar. Yetenek dosyası bir kez yazılır, ajan koşuda sadece ilgili adımda okur.
2. **Ajanın hatırlaması.** Ajanın hafızası yok; oturum kapanınca her şey gider. `defter.md` dünü,
   `skills/` ise **nasıl yapıldığını** hatırlar. Yazmadığın şey olmamıştır.
3. **Ajanın gelişmesi.** Her yetenek dosyasının sonunda `## Öğrenilenler` bölümü var. Ajan koşuda aldığı
   veriyle **kendini geliştirir**: dersi `defter.md`'ye yazar, aynı ders üç koşuda tekrar ederse yeteneğin
   `## Öğrenilenler` bölümüne öneri bırakır. Kararı patron verir. Pazartesi öğrenilen, salı davranışa döner.

## Katalog

| Takım            | Yetenek                                                                                     | Ne işe yarar                                                                                    | Kaynak                                                                                                                                                                                                          | Lisans |
| ---------------- | ------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| `x-icerik`       | [`kaynak-dogrulama`](../skills/kaynak-dogrulama/SKILL.md)                                   | Her iddiayı birincil kaynağa açıp ✅/🟡/⛔ ile sınıflar.                                          | kendi üretimimiz                                                                                                                                                                                                | —      |
| `x-icerik`       | [`iddia-ayristirma-ve-kanit-defteri`](../skills/iddia-ayristirma-ve-kanit-defteri/SKILL.md) | Metni kontrol edilebilir iddialara böler ve izi sürülebilir kanıt defteri tutar.                | [petar-nauka/fact-check-skill · SKILL.md](https://github.com/petar-nauka/fact-check-skill/blob/main/SKILL.md)                                                                                                   | MIT    |
| `x-icerik`       | [`kaynak-kimlik-dogrulama`](../skills/kaynak-kimlik-dogrulama/SKILL.md)                     | SIFT ile kaynağın kimliğini, materyalin gerçekliğini ve iddiayı desteklediğini ayrı ayrı sınar. | [jamditis/claude-skills-journalism · journalism-core/skills/source-verification/SKILL.md](https://github.com/jamditis/claude-skills-journalism/blob/master/journalism-core/skills/source-verification/SKILL.md) | MIT    |
| `youtube-analiz` | [`analitik-okuma-ve-raporlama`](../skills/analitik-okuma-ve-raporlama/SKILL.md)             | Ham izleyici verisini kaynaklı, üç öneriyle biten bir rapora çevirir.                           | [social-media-skills/skills · skills/analytics-and-reporting/SKILL.md](https://github.com/social-media-skills/skills/blob/main/skills/analytics-and-reporting/SKILL.md)                                         | MIT    |
| `youtube-analiz` | [`icerik-denetimi`](../skills/icerik-denetimi/SKILL.md)                                     | 90 günlük içeriği tut/bırak/tazele diye triyaj eder ve tutulmayan sözleri bulur.                | [social-media-skills/skills · skills/content-audit/SKILL.md](https://github.com/social-media-skills/skills/blob/main/skills/content-audit/SKILL.md)                                                             | MIT    |
| `twitter-icerik` | [`x-article-format`](../skills/x-article-format/SKILL.md)                                   | X Article paketinin biçim otoritesi: uzunluk, iskelet, tablo yasağı, kontrol listesi.           | kendi üretimimiz                                                                                                                                                                                                | —      |
| `twitter-icerik` | [`anlati-kurgusu`](../skills/anlati-kurgusu/SKILL.md)                                       | İşin içindeki gerçek hikâyeyi bulur ve üç beatlik yaya oturtur; hikâye uydurmayı yasaklar.      | [social-media-skills/skills · skills/storytelling-and-narrative/SKILL.md](https://github.com/social-media-skills/skills/blob/main/skills/storytelling-and-narrative/SKILL.md)                                   | MIT    |
| `twitter-icerik` | [`zincir-yazimi`](../skills/zincir-yazimi/SKILL.md)                                         | X zinciri ve lansman postu yazar; tek post daha güçlüyse bunu söyler.                           | [social-media-skills/skills · skills/thread-writer/SKILL.md](https://github.com/social-media-skills/skills/blob/main/skills/thread-writer/SKILL.md)                                                             | MIT    |
| `twitter-icerik` | [`kaynak-dogrulama`](../skills/kaynak-dogrulama/SKILL.md)                                   | Her iddiayı birincil kaynağa açıp ✅/🟡/⛔ ile sınıflar.                                          | kendi üretimimiz                                                                                                                                                                                                | —      |

**Toplam 8 yetenek, 3 takım.**

## Nereden aldık

| Depo | Ne | Lisans | Kaç yetenek |
|---|---|---|---|
| [social-media-skills/skills](https://github.com/social-media-skills/skills) | Sosyal medya skill'leri (yazım, analitik, denetim) | MIT | 4 |
| [petar-nauka/fact-check-skill](https://github.com/petar-nauka/fact-check-skill) | Fact-checking ve kanıt defteri | MIT | 1 |
| [jamditis/claude-skills-journalism](https://github.com/jamditis/claude-skills-journalism) | Gazetecilik: doğrulama ve kaynak | MIT | 1 |

`kaynak-dogrulama` ve `x-article-format` bu kitin kendi üretimidir; dış kaynağı yoktur.

Dışarıdan alınan her yetenek dosyasının sonunda **`## Kaynak ve değişiklikler`** bölümü var:
orijinalden ne alındı, ne değiştirildi. Değişikliklerin ortak yönü:
- **ANAYASA §1** gereği yayınlama / mail / zamanlama / para adımları çıkarıldı — hepsi insanda.
- **ANAYASA §2** gereği kaynağı açılmamış üçüncü taraf sayıları çıkarıldı; ✅/🟡/⛔ etiketleme eklendi;
  kişisel veri (kullanıcı adı, e-posta) yasağı eklendi.
- **ANAYASA §5** gereği takımlar arası mesajlaşma çıkarıldı; çıktı dosyaya yazılır, okuyan okur.
- Dış araç zincirleri çıkarıldı; girdi/çıktı yolları bu reponun dosya sözleşmesine bağlandı.

## Nasıl çalışır (teknik)

- Kaynak: `takimlar/<takim>/takim.md` frontmatter'ındaki `skills: [ad1, ad2]` alanı.
- `bin/agents_uret.py` bu alanı **şirket alanı** sayar (agent frontmatter'ına sızmaz) ve önsöze
  `Yeteneklerin: ...` satırını ekler.
- `bin/kos.py` `istem()` aynı satırı koşu istemine koyar — `python3 bin/kos.py <takim> --kuru` ile görülür.
- Bağın bütünlüğünü `tests/test_skills.py` denetler: bildirilen her yetenek diskte var mı, her yetenek
  hangi takımı bildiriyorsa o takım da onu bildiriyor mu, her dosya `## Öğrenilenler` taşıyor mu,
  bu katalog güncel mi.
