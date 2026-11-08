#!/usr/bin/env python3
"""Apify aktör istemcisi — stdlib, anahtar yalnızca ortamdan (`APIFY_TOKEN`).

Kullanım:
    python3 bin/apify_cek.py <aktor_id> '<json girdi>' [--max 50] [--zaman-asimi 300]

Örnek:
    python3 bin/apify_cek.py apidojo/youtube-scraper '{"youtubeHandles":["@ornek-kanal"]}' --max 5

Kural: token ne URL'ye, ne loga, ne çıktıya yazılır — yalnızca `Authorization` başlığında taşınır.
Hata durumunda istisna fırlatmaz, `{"hata": ..., "detay": ...}` sözlüğü döner.
Aktörler PAY_PER_EVENT ile ücretlendirilir: her çağrı para harcar. Önce `--max` ile küçük dene.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

TABAN = "https://api.apify.com/v2"
SENKRON_TAVAN_SN = 300   # run-sync uç noktasının üst sınırı


def _kimlik(aktor_id):
    """`kullanici/aktor` → `kullanici~aktor` (Apify URL biçimi)."""
    return urllib.parse.quote(aktor_id.replace("/", "~"), safe="~")


def _sorgu(**parametreler):
    temiz = {k: v for k, v in parametreler.items() if v is not None}
    return ("?" + urllib.parse.urlencode(temiz)) if temiz else ""


def _istek(token, url, govde=None, zaman_asimi_sn=60):
    """Tek HTTP çağrısı. Başarıda ayrıştırılmış JSON, hatada `{"hata": ...}`."""
    veri = json.dumps(govde, ensure_ascii=False).encode("utf-8") if govde is not None else None
    basliklar = {"Authorization": "Bearer " + token, "User-Agent": "a-sirketi/1.0"}
    if veri is not None:
        basliklar["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=veri, headers=basliklar),
                                    timeout=zaman_asimi_sn) as yanit:
            metin = yanit.read().decode("utf-8")
        return json.loads(metin) if metin.strip() else {}
    except urllib.error.HTTPError as exc:
        return {"hata": f"HTTP {exc.code}", "detay": exc.read().decode("utf-8", "ignore")[:300]}
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
        return {"hata": type(exc).__name__}


def aktor_calistir(token, aktor_id, girdi, zaman_asimi_sn=SENKRON_TAVAN_SN, max_items=None):
    """Aktörü koşturup dataset öğelerini liste olarak döner; hatada `{"hata": ...}`.

    En fazla 300 sn — daha uzun işler için Apify'ın async koş+yokla yolu gerekir, bu kitte yok."""
    if not token:
        return {"hata": "APIFY_TOKEN yok"}
    sure = min(int(zaman_asimi_sn), SENKRON_TAVAN_SN)
    url = (f"{TABAN}/acts/{_kimlik(aktor_id)}/run-sync-get-dataset-items"
           + _sorgu(timeout=sure, maxItems=max_items))
    sonuc = _istek(token, url, govde=girdi, zaman_asimi_sn=sure + 30)
    if isinstance(sonuc, list):
        return sonuc
    return sonuc if isinstance(sonuc, dict) and "hata" in sonuc else {"hata": "beklenmeyen yanıt"}


def maliyet_topla(token, baslangic_iso, limit=50):
    """`baslangic_iso`'dan sonra başlayan koşuların toplam USD maliyeti; okunamazsa None."""
    yanit = _istek(token, f"{TABAN}/actor-runs" + _sorgu(limit=limit, desc="true"), zaman_asimi_sn=30)
    if not isinstance(yanit, dict) or "hata" in yanit:
        return None
    ogeler = ((yanit.get("data") or {}).get("items")) or []
    yeni = [o for o in ogeler if (o.get("startedAt") or "") >= baslangic_iso]
    return round(sum(float(o.get("usageTotalUsd") or 0) for o in yeni), 4)


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        print("APIFY_TOKEN yok (.env)", file=sys.stderr)
        return 1
    try:
        girdi = json.loads(argv[1])
    except ValueError:
        print("girdi JSON değil", file=sys.stderr)
        return 2
    azami = int(argv[argv.index("--max") + 1]) if "--max" in argv else None
    sure = int(argv[argv.index("--zaman-asimi") + 1]) if "--zaman-asimi" in argv else SENKRON_TAVAN_SN
    sonuc = aktor_calistir(token, argv[0], girdi, zaman_asimi_sn=sure, max_items=azami)
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    return 1 if isinstance(sonuc, dict) and "hata" in sonuc else 0


if __name__ == "__main__":
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import ayar  # noqa: E402

    ayar.ortam_yukle()
    sys.exit(main(sys.argv[1:]))
