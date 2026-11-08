# mycompany — anı

8 Kasım 2026'da tek günde kurulan, sonra rafa kaldırılan ajan şirketi. Artık kullanılmıyor;
bu depo hatıra olarak duruyor.

## Ne vardı

- **CEO Fable 5.1** ve üç aileden **12 ajan**:
  Claude (Opus, Sonnet, Haiku 5.5) · Antigravity (Opus, Sonnet, GPT-OSS 120B, Gemini 3.8 Flash,
  Gemini 4 Argon) · Codex (GPT-5.6 Luna, GPT-5.6 Terra, GPT-6 Luna, ChatGPT).
  Patron Fable'a iş verir, Fable böler, `bin/ekip.py` ile ajanlara dağıtır, sonuçları
  doğrulayıp tek rapor yazardı (`bin/ceo.py`).
- **Piksel ofis haritası** (`ofis/`, `bin/ofis_sunucu.py`): solda ekip salonu (arkada Codex,
  ortada Antigravity, önde Claude, en önde halıda Fable), sağda patronun özel odası. Binalar,
  masalar ve 13 karakter Codex'in görsel üretimiyle çizildi.
- Altında, iskeleti [selmakcby/a-sirketi](https://github.com/selmakcby/a-sirketi)'den gelen üç
  takımlı içerik şirketi (Telegram, X, YouTube); API anahtarı istediği için kapalı kaldı.

## Bir kez daha görmek için

```bash
python3 bin/ofis_sunucu.py
```

Tarayıcıda http://127.0.0.1:3210 (Ctrl+C ile kapanır). Harita canlı durumunu `~/.cubicle/`
altına yazar; işin bitince o klasörü silebilirsin.

## Lisans

Kod MIT; özgün iskelet ve lisans metni [LICENSE](LICENSE)'ta, A Şirketi yazarına ait.
