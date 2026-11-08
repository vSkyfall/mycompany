# P5b · `youtube-analiz` — `takim.md`

**Ne zaman:** `x-icerik` yazıldıktan sonra. Zaman daralırsa atlanabilecek tek takım budur —
zinciri göstermek için `x-icerik` + `twitter-icerik` yeter.

```
takimlar/youtube-analiz/takim.md dosyasını doldur.
Frontmatter: name: youtube-analiz · description: tek cümle, ajanın mesleği · model: sonnet · tools: [Read, Write, Glob, Grep, Bash(python3 bin/youtube_analiz_cek.py *)] · gerekli_anahtarlar: [APIFY_TOKEN] · butce_usd: 2 · skills: [analitik-okuma-ve-raporlama, icerik-denetimi]
Akan şey: python3 bin/youtube_analiz_cek.py --son-7g kanalın (.env KANAL) son videolarını ve yorumlarını veri/YYYY-Www.json dosyasına çeker. Çıktı cikti/YYYY-Www-rapor.md.
Koşu adımları: (1) veri dosyası bugünden tazeyse yeniden çekme, yoksa çekiciyi koş. (2) skills/analitik-okuma-ve-raporlama ile raporu yaz: her sayının yanında [veri/…json] etiketi; veride olmayan sayı yazılmaz, "ölçülmedi" denir. (3) Yorum temalarını isimsiz çıkar; skills/icerik-denetimi ile hangi video ne yapmış üç satır. (4) deney takımı için 3 öneri. (5) durum.json'a yt-<hafta> maddesi tamam. (6) Deftere en fazla bir ders. (7) Koşu kaydı: kaç video, kaç yorum, maliyet (Apify birkaç sent), dosya yolları.
Asla: yoruma cevap yazmaz, ölçülmemiş yargı vermez, kişi adı yazmaz, APIFY_TOKEN yoksa "eksik anahtar" deyip koşuyu hata olarak kapatır, uydurmaz.
Yetenekler bölümü: adım 2 ve 3. Türkçe, kısa.
```

> **Repoyu klonladıysan:** [`takimlar/youtube-analiz/takim.md`](../takimlar/youtube-analiz/takim.md)
> zaten dolu.

**Beklenen çıktı:** Haftalık kulvarda dönen bir takım dosyası: veri tazeyse yeniden çekmeyen,
her sayıyı kaynak dosyasına bağlayan, yorumları isimsiz kümeleyen yedi adım.

**Dikkat:** Retention ve CTR bu yolda **ölçülmez** (Analytics API + OAuth gerekir); rapora
"ölçülmedi" yazılır, tahmin edilmez — [`bin/youtube_analiz_cek.py`](../bin/youtube_analiz_cek.py).
Apify aktörleri her çağrıda para harcar.
