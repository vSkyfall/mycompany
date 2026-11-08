#!/usr/bin/env python3
"""Bir X linkinin metnini giriş yapmadan çeker (fxtwitter aynası). Tarayıcı yok, hesap riski yok.

Kullanım: python3 bin/tweet_cek.py <link> [...]   → JSON listesi

Ayna ulaşılamazsa kayıt `kaynak: cekilemedi` döner; ajan bunu ⛔ ile işaretler, uydurmaz.
X Article (uzun yazı) gövdesini ayna çoğu zaman **vermez**: `makale` alanı null gelir, elde yalnızca
özet metin kalır. O durumda iddia doğrulaması için ekran görüntüsü ya da birincil kaynak gerekir.
"""
import json
import re
import sys
import urllib.error
import urllib.request

DURUM = re.compile(r"https?://(?:www\.)?(?:x|twitter)\.com/([A-Za-z0-9_]+)/status/(\d+)")


def durum_parcala(link):
    eslesme = DURUM.search(link or "")
    return (eslesme.group(1), eslesme.group(2)) if eslesme else None


def _json_getir(url):
    istek = urllib.request.Request(url, headers={"User-Agent": "a-sirketi/1.0"})
    try:
        with urllib.request.urlopen(istek, timeout=20) as yanit:
            return json.loads(yanit.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return None


def tweet_cek(link):
    parca = durum_parcala(link)
    bos = {"link": link, "kaynak": "cekilemedi", "yazar": None, "metin": None,
           "makale": None, "tarih": None, "goruntulenme": None}
    if not parca:
        return {**bos, "kaynak": "x-linki-degil"}
    kullanici, kimlik = parca
    veri = _json_getir(f"https://api.fxtwitter.com/{kullanici}/status/{kimlik}")
    tweet = (veri or {}).get("tweet") if veri and veri.get("code") == 200 else None
    if not tweet:
        return bos
    yazar = tweet.get("author") or {}
    makale = tweet.get("article")
    return {"link": tweet.get("url") or link, "kaynak": "fxtwitter",
            "yazar": "@" + (yazar.get("screen_name") or kullanici),
            "metin": tweet.get("text"),
            "makale": makale.get("content") if isinstance(makale, dict) else None,
            "tarih": tweet.get("created_at"), "goruntulenme": tweet.get("views")}


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    print(json.dumps([tweet_cek(link) for link in argv], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
