# P4 · Üç takımı aç

**Ne zaman:** Anayasa yazıldıktan hemen sonra.

```
bin/takim-olustur.sh betiğiyle üç takım oluştur: x-icerik, youtube-analiz, twitter-icerik. Sonra `ls takimlar/*/` çıktısını göster; her takımda dört dosya olmalı: takim.md, kurallar.md, defter.md, durum.json.
```

> **Repoyu klonladıysan:** üç takım zaten açık. Aynı betikle dördüncü bir takım açabilirsin:
> `bin/takim-olustur.sh <yeni-takim>` (bkz. `docs/05-yeni-takim.md`).

**Beklenen çıktı:** `takimlar/` altında üç klasör, her birinde iskeletten gelen dört dosya —
içleri `TAKIM` yerine takımın adıyla doldurulmuş hâlde. `takim.md`'lerin gövdesi hâlâ boş; onları
P5a-P5c dolduracak.

**Dikkat:** Takım adı ASCII kebab-case olmalı; betik değilse reddeder. Aynı ada ikinci kez
çalıştırılırsa "zaten var" der, üstüne yazmaz.
