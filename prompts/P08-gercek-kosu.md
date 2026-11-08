# P8 · Gerçek koşu — telefondan link

**Ne zaman:** Kuru koşu temiz çıktıktan sonra. Önce telefonundan bota bir X linki + kısa bir not
gönder, sonra bu prompt'u ver.

```
python3 bin/telegram_oku.py --son 5 ile son mesajları göster. Sonra BİR KEZ python3 bin/telegram_oku.py --isle koş ve takimlar/x-icerik/gelen/ altında oluşan dosyayı göster. Sonra python3 bin/kos.py x-icerik koştur; bitince takimlar/x-icerik/kosu/ altındaki bugünkü kaydın "## Bekçi" bölümünü ve durum.json kuyruğunu göster. Kayıt 2-4 dakika sürer, bekle.
```

> **Repoyu klonladıysan:** aynı akış geçerli. `bin/telegram_dinle.py` açıksa `--isle` adımına
> gerek kalmaz: mesaj düştüğü an `gelen/` yazılır ve koşu kendiliğinden başlar.

**Beklenen çıktı:** `gelen/` altında linki ve notunu taşıyan bir JSON; `kosu/` altında bugünkü
koşu kaydı; kaydın altında `## Bekçi — karar: kabul` ya da `red`; `durum.json` kuyruğunda
`x-<update_id>` maddesi.

**Dikkat:** İkinci kez `--isle` boş döner — hata değil, Telegram aynı güncellemeyi ikinci kez
vermez (offset `durum.json` → `sayaclar.telegram_son_update` alanında durur). Bekçi red verirse
bu iyi haberdir: denetim ilk koşuda çalıştı demektir; ajan aynı oturumda düzeltmeye gider
(en fazla iki kez). Beklerken olan şu: ajan anayasayı, kim olduğunu, kurallarını ve yeteneğini
okur; defteri boş, bu ilk koşu.
