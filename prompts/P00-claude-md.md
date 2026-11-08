# P0 · `CLAUDE.md` — projeye kimlik ver

**Ne zaman:** İlk adım. Klasör boş, Claude Code yeni açıldı; henüz tek bir dosya bile yok.

```
Çalışma klasörü ~/a-sirketi. Bu klasör "A şirketi": her gün elle yaptığım işleri yapan üç yapay zekâ ajanından oluşan küçük bir şirket. Kök dizine CLAUDE.md yaz:
- Ne bu: üç takım (x-icerik, youtube-analiz, twitter-icerik), bir bekçi, bir dağıtıcı, kapalı döngü. Yayın düğmesi insanda.
- Okuma sırası (her ajan her koşuda): ANAYASA.md → sirket/AJAN-KIMLIGI.md → takimlar/<takim>/kurallar.md → takimlar/<takim>/takim.md → skills/.
- Klasör yapısı: bin/ (koşu sürücüsü kos.py, bekçi bekci.py, dağıtıcı dagitici.py), takimlar/<takim>/ (takim.md, kurallar.md, defter.md, durum.json, kosu/, cikti/), skills/<ad>/SKILL.md (yetenekler; her birinde kaynak ve lisans yazar), sirket/ (ajan kimliği), .env (anahtarlar; asla commit'e girmez).
- Yasaklar: .env okuma/yazdırma, sosyal hesaba yazma, mail gönderme, para harcama, ANAYASA.md ve kurallar.md'yi ajanın değiştirmesi.
Türkçe, kısa, en fazla 40 satır.
```

> **Repoyu klonladıysan:** [`CLAUDE.md`](../CLAUDE.md) zaten yerinde. Bu prompt'u ancak kendi
> şirketini kurarken kullanırsın.

**Beklenen çıktı:** Kök dizinde kırk satırı geçmeyen bir `CLAUDE.md`. Claude Code o klasörde her
açıldığında bu dosyayı okur — yani projenin ilk kuralı, ilk dosyası olur.

**Dikkat:** Bu dosya ajanların okuma sırasının bir parçası değil (o sıra `ANAYASA.md` ile başlar);
`CLAUDE.md` Claude Code'un kendisi içindir.
