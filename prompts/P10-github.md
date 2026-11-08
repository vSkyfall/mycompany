# P10 · GitHub

**Ne zaman:** Döngü bir kez baştan sona döndükten sonra.

```
git add -A && git status çıktısını göster; .env listede OLMAMALI. Sonra "feat: A şirketi — üç ajan, bir bekçi, bir döngü" mesajıyla commit at. Sonra gh repo create a-sirketi --public --source=. --push ile repoyu aç ve adresi ver.
```

> **Repoyu klonladıysan:** bu adım kendi kopyan içindir. Depo adını kendi adınla değiştir;
> `gh` kurulu ve giriş yapılmış olmalı.

**Beklenen çıktı:** `.env` içermeyen bir commit ve public bir GitHub deposu.

**Dikkat:** `git status` çıktısında `.env` görünüyorsa **dur** — `.gitignore` yerinde değil
demektir. Koşu kayıtları, çıktılar, gelen mesajlar ve veri dosyaları da `.gitignore` kapsamındadır
(`takimlar/*/kosu/`, `cikti/`, `gelen/`, `veri/`): şirketin ürettiği içerik repoya girmez.
`tests/test_kit.py` bunu ayrıca denetler — repoda anahtara benzeyen bir metin varsa test kırmızı döner.
