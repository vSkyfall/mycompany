#!/usr/bin/env python3
"""YouTube çekici — kanalın son videoları + yorumları, Apify aktörleriyle (Google API anahtarı yok).

Kullanım: python3 bin/youtube_analiz_cek.py [--son-7g | --son-30g] [--yorum 50]
          [--kanal @baska-kanal] [--azami-video 50]
Çıktı: takimlar/youtube-analiz/veri/YYYY-Www.json (aynı hafta üzerine yazar) + stdout özet.

Kanal `.env` içindeki `KANAL` değerinden gelir; `--kanal` onu geçersiz kılar.
Anahtar: `APIFY_TOKEN`. Retention ve CTR **hiçbir** yolda yok (Analytics API + OAuth gerekir):
rapora "ölçülmedi" yazılır, tahmin edilmez.
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import apify_cek  # noqa: E402
import ayar  # noqa: E402

AKTOR_VIDEO = "apidojo/youtube-scraper"
AKTOR_YORUM = "apidojo/youtube-comments-scraper"
AZAMI_VIDEO = 50
CARPAN = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}


def _sayi(deger):
    try:
        return int(float(deger))
    except (TypeError, ValueError):
        return 0


def abone_sayisi(metin):
    """"8.03K subscribers" → 8030. Yuvarlanmış gelir; ayrıştırılamazsa None (uydurulmaz)."""
    eslesme = re.search(r"([\d.,]+)\s*([KMB])?", str(metin or ""))
    if not eslesme:
        return None
    try:
        taban = float(eslesme.group(1).replace(",", ""))
    except ValueError:
        return None
    return round(taban * CARPAN.get((eslesme.group(2) or "").upper(), 1))


def sure_iso(saniye):
    """3096 → "PT51M36S"."""
    toplam = _sayi(saniye)
    if not toplam:
        return None
    saat, kalan = divmod(toplam, 3600)
    dakika, sn = divmod(kalan, 60)
    return "PT" + (f"{saat}H" if saat else "") + (f"{dakika}M" if dakika else "") + (f"{sn}S" if sn else "")


def _utc(zaman_metni):
    try:
        return datetime.fromisoformat(str(zaman_metni).replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def video_esle(oge):
    """Apify öğesi → sade şema."""
    yayin = _utc(oge.get("publishDate") or oge.get("uploadDate"))
    return {"id": oge.get("id"), "baslik": oge.get("title"),
            "yayin": yayin.isoformat().replace("+00:00", "Z") if yayin else None,
            "sure": sure_iso(oge.get("duration")), "goruntulenme": _sayi(oge.get("views")),
            "begeni": _sayi(oge.get("likes")), "yorum_sayisi": _sayi(oge.get("comments"))}


def kanal_esle(ogeler):
    """Video öğelerinin içindeki kanal bloğundan kanal özeti.
    Kanal toplam görüntülenmesi aktörde yok → null kalır, uydurulmaz."""
    kanal = next((o.get("channel") for o in ogeler if isinstance(o.get("channel"), dict)), {}) or {}
    return {"id": kanal.get("id"), "ad": kanal.get("name"),
            "abone": abone_sayisi(kanal.get("subscriberCount")),
            "abone_metin": kanal.get("subscriberCount"), "toplam_goruntulenme": None}


def tarihe_gore_sun(videolar, son_gun):
    """Eşikten yeni videolar, yeniden eskiye. Tarih filtresi yerelde (aktörde ücretli eklenti)."""
    esik = datetime.now(timezone.utc) - timedelta(days=son_gun)
    yeni = [v for v in videolar if v.get("yayin") and (_utc(v["yayin"]) or esik - timedelta(days=1)) >= esik]
    return sorted(yeni, key=lambda v: v["yayin"], reverse=True)


def videolar_cek(token, handle, son_gun, azami=AZAMI_VIDEO):
    girdi = {"youtubeHandles": [handle if handle.startswith("@") else "@" + handle],
             "includeShorts": True, "maxItems": azami}
    ogeler = apify_cek.aktor_calistir(token, AKTOR_VIDEO, girdi, max_items=azami)
    if isinstance(ogeler, dict):
        return ogeler
    videolar = [video_esle(o) for o in ogeler if o.get("type") == "video" and o.get("id")]
    return {"kanal": kanal_esle(ogeler), "videolar": tarihe_gore_sun(videolar, son_gun)}


def yorumlar_cek(token, video_id, adet):
    """Tek videonun en beğenilen yorumları. Yazar adı taşınmaz — kişi adı çıktıya girmez."""
    girdi = {"startUrls": [f"https://www.youtube.com/watch?v={video_id}"],
             "sort": "top", "maxItems": adet, "includeReplies": False}
    ogeler = apify_cek.aktor_calistir(token, AKTOR_YORUM, girdi, max_items=adet)
    if isinstance(ogeler, dict):
        return []
    return [{"metin": o.get("text", ""), "begeni": _sayi(o.get("likeCount")),
             "tarih": o.get("publishedTime"), "yanit_sayisi": _sayi(o.get("replyCount"))}
            for o in ogeler if o.get("type") == "comment"]


def _video_yorumlari(token, video, adet):
    """Aktör nadiren boş liste dönüyor; bir kez daha denenir."""
    if not adet or not video.get("yorum_sayisi"):
        return []
    return yorumlar_cek(token, video["id"], adet) or yorumlar_cek(token, video["id"], adet)


def topla(token, handle, son_gun, yorum_adet, azami=AZAMI_VIDEO):
    sonuc = videolar_cek(token, handle, son_gun, azami)
    if "hata" in sonuc:
        return sonuc
    videolar = [{**v, "yorumlar": _video_yorumlari(token, v, yorum_adet)} for v in sonuc["videolar"]]
    return {"cekim_zamani": ayar.simdi_iso(), "kaynak": f"apify:{AKTOR_VIDEO}+{AKTOR_YORUM}",
            "son_gun": son_gun, "kanal": sonuc["kanal"], "videolar": videolar}


def hafta_dosyasi(kok, zaman=None):
    yil, hafta, _ = (zaman or datetime.now(timezone.utc)).isocalendar()
    return Path(kok) / "takimlar/youtube-analiz/veri" / f"{yil}-W{hafta:02d}.json"


def _bayrak(argv, ad, varsayilan):
    try:
        return int(argv[argv.index(ad) + 1]) if ad in argv else varsayilan
    except (IndexError, ValueError):
        return varsayilan


def main(argv):
    ayar.ortam_yukle()
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        print(json.dumps({"hata": "APIFY_TOKEN yok (.env)"}, ensure_ascii=False), file=sys.stderr)
        return 1
    handle = argv[argv.index("--kanal") + 1] if "--kanal" in argv else ayar.kanal()
    basladi = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    veri = topla(token, handle, 30 if "--son-30g" in argv else 7,
                 _bayrak(argv, "--yorum", 50), _bayrak(argv, "--azami-video", AZAMI_VIDEO))
    if "hata" in veri:
        print(json.dumps(veri, ensure_ascii=False), file=sys.stderr)
        return 1
    veri["maliyet_usd"] = apify_cek.maliyet_topla(token, basladi)
    yol = hafta_dosyasi(ayar.KOK)
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"dosya": str(yol.relative_to(ayar.KOK)), "video": len(veri["videolar"]),
                      "yorum": sum(len(v["yorumlar"]) for v in veri["videolar"]),
                      "maliyet_usd": veri["maliyet_usd"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
