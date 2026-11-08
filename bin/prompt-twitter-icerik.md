## Bu koşuda

Kuyruktaki `aci-<id>` maddesinden **tek bir X Article paketi** çıkar. Paket hazır durur; yayınlayan sensin.
Bütün adımlarda `takimlar/twitter-icerik/kurallar.md` geçerlidir: tablo yok, kişi adı yok, kaynaksız sayı yok.

Tarih = bugünün `YYYY-MM-DD` değeri. Slug = konunun ASCII kebab-case hâli (Türkçe karakter yok).
Klasör: `takimlar/twitter-icerik/cikti/<tarih>-<slug>/` — klasör zaten varsa **dur**, (d)'ye geç.

### (a) Konu seç — en fazla bir tane
Adaylar, sırayla:
- `durum.json` kuyruğundaki `aci-<id>` maddeleri (dağıtıcı x-icerik'ten taşıdı).
- `takimlar/x-icerik/cikti/*.md` — `## Karar` bölümünde "yazıya değer" diyen doğrulama tabloları.
  Bu tablolar hazır kanıt taşır: oradaki ✅/🟡/⛔ etiketleri korunur, konu yeniden araştırılmaz.
- `takimlar/youtube-analiz/cikti/*-rapor.md` — bir yorum teması yazıya dönüyorsa.

Seçim ölçütü (`skills/x-article-format/SKILL.md` §1): konu tek gözlemden büyükse, adım adım kurulan
bir sistem varsa ya da okurun uygulayabileceği bir reçete çıkıyorsa article olur. Tek keskin gözlem
article değildir — o posttur. **Hiçbiri geçmiyorsa paket üretme**, (d)'ye geç ve sebebi yaz.

### (b) Formatı oku
`skills/x-article-format/SKILL.md` — iskelet, uzunluk, tablo yasağı, görsel işareti, lansman postu,
kontrol listesi. Otorite budur.

### (c) Paketi yaz
1. **`article.md`** — arşiv/çalışma kopyası. Gövde 1.000-2.000 kelime, 3-7 bölüm, her bölüm tek fikir,
   başlık gövdeye yazılmaz, tablo yok, kod bloğu yok (çok satırlı komut görsele gider).
   Görsel yerleri kendi satırında: `[GÖRSEL n: <dosya-adi>.png — ne anlattığı]`.
2. **`article.html`** — paketin **birincil** dosyası. Tek dosya, dışarıdan hiçbir yerel dosya çekmez:
   görseller `<img src="data:image/png;base64,…">` olarak gömülüdür. En üstte sabit (`position: sticky`)
   bir çubukta **📋 Tüm makaleyi kopyala** butonu durur; `copyArticle()` panoya hem `text/html` hem
   `text/plain` yazar. Kopyalanabilir alanda yalnızca X Article'ın taşıdığı etiketler kalır:
   `h2, h3, p, strong, em, s, ul, ol, li, blockquote, a, hr`. Sayfanın kendi notları o alanın dışındadır.
   Görsel henüz yoksa `[GÖRSEL n: …]` işaret satırı `<p>` olarak kalır.
3. **Kapak** — `python3 bin/kapak_uret.py "<başlık>" takimlar/twitter-icerik/cikti/<tarih>-<slug>/kapak.png`
   Çıkış 0 → 3840×736 kapak hazır. Çıkış 2 (FAL_KEY yok) ya da 1 → dosya yoktur; `00-BURADAN-BASLA.md`
   içine **`kapak: sen ekleyeceksin`** satırını yaz ve devam et. Anahtarı okumaya, basmaya çalışma.
4. **`00-BURADAN-BASLA.md`** — `Başlık:` (6-12 kelime, gövdede geçmez), yedek başlık, kapak durumu,
   **YAYIN GÜNÜ adımları** (kapağı yükle → `article.html`'i tarayıcıda aç, 📋 ile kopyala, X Article
   gövdesine yapıştır → görselleri `GÖRSEL` işaretlerinin yerine koy → son okuma → yayınla → lansman
   postu → 3-6 saat sonra quote repost), görsel listesi (numara, dosya, hangi bölüm, ne anlattığı,
   `üretildi`/`bekliyor`), lansman postu 3 varyant + quote repost 3 varyant, karakter sayıları,
   kaynaklar (hangi iddia hangi dosyadan).

### (d) Kuyruğu kapat
İşlediğin `aci-<id>` maddesinin `durum` alanını `tamam` yap ve `not` alanına paket klasörünü yaz.
Konu yoksa madde `tamam` olur ama `not` sebebi söyler (hangi kaynaklara bakıldı, aday neden elendi —
"tek gözlem, post olur" gibi).

### Bitirmeden önce
`x-article-format` §6 kontrol listesini paket üzerinde geç: tablo yok · markdown link yok ·
iç içe liste yok · başlık gövdede değil · her görsel işareti tek satırda · lansman postu link payıyla
255 karakter altında · quote varyantları lansmanı tekrar etmiyor · uydurma sayı yok.
