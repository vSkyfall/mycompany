# P5c · `twitter-icerik` — `takim.md`

**Ne zaman:** Üç `takim.md`'nin sonuncusu; zincirin ikinci ucu.

```
takimlar/twitter-icerik/takim.md dosyasını doldur.
Frontmatter: name: twitter-icerik · description: tek cümle, ajanın mesleği · model: sonnet · tools: [Read, Write, Glob, Grep, Bash(python3 bin/kapak_uret.py *)] · gerekli_anahtarlar: [] · butce_usd: 3 · skills: [x-article-format, zincir-yazimi, anlati-kurgusu, kaynak-dogrulama]
Akan şey: Girdi durum.json kuyruğunda dağıtıcının düşürdüğü aci-<id> maddesi (x-icerik'in "yazıya değer" kararı ve doğrulama tablosu). Çıktı cikti/<tarih>-<slug>/ altında article.md, article.html (📋 kopyala butonu), kapak.png.
Koşu adımları: (1) Kuyruktaki aci-<id> maddesini ve x-icerik'in tablosunu oku. (2) skills/anlati-kurgusu ile omurgayı kur; skills/x-article-format ile article.md yaz: 1.000-2.000 kelime, tablo yok, kişi adı yok, her iddia etiketli — tablodaki ⛔ iddia yazıya girmez. (3) article.html üret (kopyala butonu). (4) python3 bin/kapak_uret.py ile kapak.png 3840×736; FAL_KEY yoksa "kapak: sen ekleyeceksin" yaz, hata verme. (5) Günde en fazla 1 paket; maddeyi tamam yap. (6) Deftere en fazla bir ders. (7) Koşu kaydı: kelime sayısı, kapak var/yok, dosya yolları, maliyet.
Asla: X'e yazmaz, yayınlamaz, yazıyı hiçbir yere göndermez; yayın düğmesi insanda.
Yetenekler bölümü: adım 2. Türkçe, kısa.
```

> **Repoyu klonladıysan:** [`takimlar/twitter-icerik/takim.md`](../takimlar/twitter-icerik/takim.md)
> zaten dolu.

**Beklenen çıktı:** Kuyruktan beslenen, günde en fazla bir paket üreten ve **yayınlamayan** bir
takım dosyası. Çıktı tek klasördür: `article.md`, `article.html`, `kapak.png`.

**Dikkat:** `FAL_KEY` yoksa `bin/kapak_uret.py` 2 ile çıkar; koşu hata vermez, pakete
"kapak: sen ekleyeceksin" notu düşer. ANAYASA §1 gereği bu takımın hiçbir adımında yayınlama yok.
