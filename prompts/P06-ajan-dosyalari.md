# P6 · Ajan dosyaları — "Sen `x-icerik` ajanısın"

**Ne zaman:** Üç `takim.md` dolduktan hemen sonra.

```
python3 bin/agents_uret.py koştur, sonra python3 bin/agents_uret.py --check. Üretilen .claude/agents/x-icerik.md dosyasının ilk 8 satırını göster.
```

> **Repoyu klonladıysan:** bu komut sende de çalışır ve çalışmalı — `takim.md`'yi her
> değiştirdiğinde ajan dosyasını yeniden üretirsin. `--check` sapma varsa 1 döner.

**Beklenen çıktı:** `.claude/agents/<takim>.md` üç dosya. İlk satır ajanın kimliğidir:
"Sen `x-icerik` ajanısın. A Şirketi'nde bir çalışansın ve bir yapay zekâ ajanısın. Mesleğin: …" —
ardından okuma sırası ve yetenek satırı gelir. `--check` çıkışı 0 olmalı.

**Dikkat:** `takim.md` tek kaynaktır; agent dosyası **üretilir**, elle düzenlenmez. Şirkete özel
frontmatter alanları (`gerekli_anahtarlar`, `butce_usd`, `skills`) agent frontmatter'ına sızmaz;
`skills` önsözdeki tek satıra dönüşür.
