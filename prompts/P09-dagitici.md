# P9 · Dağıtıcı — zincir

**Ne zaman:** `x-icerik` koşusu "yazıya değer" kararıyla kapandıktan sonra; döngünün kapandığı an.

```
Önce python3 bin/dagitici.py --kuru koştur ve ZİNCİR satırını göster (x-<id> → aci-<id>). Sonra python3 bin/dagitici.py koştur: twitter-icerik arka planda koşacak (3-5 dakika). Bitince cikti/ altındaki article.html yolunu ver ve kosu/ kaydındaki bekçi kararını göster.
```

> **Repoyu klonladıysan:** aynı komutlar. Zincirin kendisi kodda değil,
> [`bin/dagitici.py`](../bin/dagitici.py) içindeki `ZINCIR` tablosundadır — yeni bir halka
> eklemek bir satırdır.

**Beklenen çıktı:** Kuru koşuda `x-<id> → twitter-icerik/aci-<id>` satırı; gerçek koşuda
`twitter-icerik` başlar ve `takimlar/twitter-icerik/cikti/<tarih>-<slug>/article.html` çıkar.
Sonuç: tek link atıldı, iki ajan koştu, iki bekçi kararı verildi, bir paket çıktı —
ve hiçbir yere yayınlanmadı.

**Dikkat:** Aynı takımı arka arkaya tetiklersen tavan devreye girebilir: takım başına günde dört
koşu, şirkete günde 10 USD, mesai 09:00–23:00 ([`bin/ayar.py`](../bin/ayar.py)). Bu bir hata değil,
ANAYASA §4'ün kanıtıdır — tavana çarpan koşu sebebini `durum.json`'a yazar, sessizce durmaz.
Takımlar birbirine mesaj atmaz; zinciri yalnızca dağıtıcı kurar (§5).
