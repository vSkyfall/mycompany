# P5a · `x-icerik` — `takim.md`

**Ne zaman:** Üç takım klasörü açıldıktan sonra; üç `takim.md`'nin ilki.

```
takimlar/x-icerik/takim.md dosyasını doldur.
Frontmatter: name: x-icerik · description: tek cümle, ajanın MESLEĞİ (bu cümle ajan dosyasının ilk satırında "Sen x-icerik ajanısın … Mesleğin: …" olarak görünecek) · model: sonnet · tools: [Read, Write, Glob, Grep, WebSearch, WebFetch, Bash(python3 bin/tweet_cek.py *), Bash(python3 bin/telegram_oku.py *)] · gerekli_anahtarlar: [TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID] · butce_usd: 2 · skills: [kaynak-dogrulama, iddia-ayristirma-ve-kanit-defteri, kaynak-kimlik-dogrulama]
Akan şey: Girdi takimlar/x-icerik/gelen/*.json — Telegram'dan gelen X linki ve notum; bunları bin/telegram_oku.py --isle yazar. Çıktı takimlar/x-icerik/cikti/YYYY-MM-DD-<update_id>-<hesap>.md: doğrulama tablosu ve karar.
Koşu adımları (numaralı): (1) python3 bin/telegram_oku.py --isle koş, yeni gelen dosyalarını listele; yeni yoksa koşu kaydına "yeni link yok" yazıp bitir. (2) Her link için python3 bin/tweet_cek.py <link>; "kaynak: cekilemedi" ise tabloyu "metin çekilemedi" notuyla ⛔ ağırlıklı yaz, tarayıcı açma, uydurma. (3) Metni skills/iddia-ayristirma-ve-kanit-defteri ile iddialara böl; skills/kaynak-dogrulama şablonuyla her iddiayı ✅/🟡/⛔ etiketle, birincil kaynağı ara — link başına en fazla 3 arama; kaynağın kimliğinden şüphe varsa skills/kaynak-kimlik-dogrulama. (4) Mesajdaki notumu kararın başına etiket olarak koy. (5) durum.json kuyruğuna x-<update_id> maddesi ekle; "yazıya değer" dediysen durumu tamam yap — dağıtıcı bu maddeyi twitter-icerik'e taşıyacak; işlenen gelen dosyasını gelen/islendi/ altına taşı. (6) defter.md'ye en fazla bir ders. (7) Koşu kaydını SIRKET_KOSU yoluna yaz: kaç link, kaç tablo, kaç ⛔, dosya yolları, maliyet.
Yetenekler bölümü: hangi adımda hangi skill okunur (adım 3).
Çıktı sözleşmesi: SKILL şablonu birebir — başlık, | İddia | Durum | Ne söylenir | tablosu, ## Karar, ## Birincil bağlantılar.
Türkçe yaz, kısa tut, uydurma adım ekleme.
```

> **Repoyu klonladıysan:** [`takimlar/x-icerik/takim.md`](../takimlar/x-icerik/takim.md) zaten
> dolu. Bu prompt'u kendi takımını yazarken şablon olarak kullan: frontmatter → akan şey →
> numaralı koşu adımları → çıktı sözleşmesi.

**Beklenen çıktı:** Frontmatter'ı eksiksiz, yedi adımlı, çıktı sözleşmesi yazılı bir `takim.md`.
`description` alanı ajanın mesleğidir — P6'da üretilecek ajan dosyasının ilk satırında görünür.

**Dikkat:** Dosyanın iskeleti hep aynıdır — meslek, akan şey, araçlar, yetenekler, adımlar, çıktı;
kurallar dosyası ayrıdır. Claude Code'un yazdığını oku, ekle-çıkar; takılırsan hazır dosyayı kopyala.
