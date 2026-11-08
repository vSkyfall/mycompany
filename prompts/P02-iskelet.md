# P2 · İskelet — betikler, bekçi, yetenekler, kimlik

**Ne zaman:** Anahtar dosyası hazır olduktan sonra, anayasadan önce.

```
~/a-sirketi-kit içinden şunları ~/a-sirketi içine kopyala: bin/ (tamamı), .claude/settings.json (bekçi hook ayarı; .claude/agents/ KOPYALAMA, onları sonra üreteceğiz), skills/ (yetenek dosyaları), sirket/ (ajan kimliği ve yetenek kataloğu), takimlar/_iskelet/ (takım şablonu), tests/. Kopyaladıktan sonra:
1) `python3 -m unittest discover -s tests` koştur, sonucu söyle.
2) skills/ altındaki her SKILL.md'nin frontmatter'ındaki name, kaynak ve lisans satırlarını tek tablo halinde göster.
3) sirket/AJAN-KIMLIGI.md'yi oku ve bana üç cümleyle özetle: ajan kim, patron kim, bekçi ne yapar.
Hiçbir dosyanın içeriğini değiştirme.
```

> **Repoyu klonladıysan:** bu prompt'a gerek yok — `bin/`, `skills/`, `sirket/`,
> `.claude/settings.json`, `tests/` ve `takimlar/_iskelet/` zaten yerinde. Aynı kontrolü
> `python3 -m unittest discover -s tests` ile kendin yaparsın.

**Beklenen çıktı:** Testler yeşil; sekiz yeteneğin adı, kaynağı ve lisansı tek tabloda; ajan
kimliğinin üç cümlelik özeti. Hiçbir dosya değişmez.

**Dikkat:** `.claude/agents/` **kopyalanmaz** — ajan dosyaları P6'da `takim.md`'lerden üretilir.
Betikler hazır araçtır, yazdırılmaz; yetenekler açık kaynaklardan uyarlandı, her dosyada kaynağı ve lisansı yazıyor ([`sirket/YETENEKLER.md`](../sirket/YETENEKLER.md)).
