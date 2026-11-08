# P1 · Klasör, git, anahtar dosyası

**Ne zaman:** `CLAUDE.md` yazıldıktan sonra, iskelet gelmeden önce.

```
~/a-sirketi içinde git başlat. ~/a-sirketi-kit/.gitignore ve ~/a-sirketi-kit/.env.example dosyalarını buraya kopyala. .gitignore'un ilk satırının ".env" olduğunu bana göster. .env.example'ı .env olarak kopyala ama İÇİNİ AÇMA, okuma, yazdırma — değerleri ben dolduracağım. Bittiğinde `git status` çıktısını göster; .env listede olmamalı.
```

> **Repoyu klonladıysan:** bu prompt'a gerek yok — `.gitignore` ve `.env.example` zaten yerinde.
> Sana düşen tek şey `cp .env.example .env` ve değerleri doldurmak
> (bkz. [KURULUM.md](../KURULUM.md) Adım 1).

**Beklenen çıktı:** `git init` yapılmış bir klasör, ilk satırı `.env` olan bir `.gitignore` ve
içi boş bir `.env`. `git status` çıktısında `.env` görünmemeli.

**Dikkat:** `.env`'i Claude Code'a **açtırma**; değerleri kendi editöründe elle yaz. Ajanın `.env` okuması `CLAUDE.md`'de de `ANAYASA.md` §2'de de yasaktır.
