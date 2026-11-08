#!/usr/bin/env python3
"""Ofis sunucusu — şirketin (mycompany) kendi ofis görünümü (ofis/index.html) ve verisi.

Yalnız 127.0.0.1'e bağlanır, bağımlılık yok (standart kütüphane). Sayfa her birkaç saniyede
`/api/durum`'u okur: takımlar, kuyruklar, bekçi kararları, son koşular, "ben yokken ne oldu".

Sayfadan yapılabilenler (hepsi şirketin kendi araçlarıyla, kuralları atlamadan):
  POST /api/gordum  {"takim"}            yayına hazır paketi aldın: el iner     (bin/ofis.py --gordum)
  POST /api/is      {"takim", "metin"}   takıma iş ver: kuyruğa `not-…` maddesi  (dagitici.kuyruga_yaz)
  POST /api/kos     {"takim"}            takımı şimdi koştur                     (bin/kos.py; mesai/tavan geçerli)

Yazma istekleri yalnız bu sayfadan kabul edilir: Host ve Origin bu sunucu olmalı, gövde JSON.

Kullanım: python3 bin/ofis_sunucu.py [--port 3210]
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402
import dagitici  # noqa: E402
import ofis  # noqa: E402

KOK = ayar.KOK
SAYFA = KOK / "ofis"
VARSAYILAN_PORT = ofis.GORUNUM_PORT
GORSEL_ADI = re.compile(r"^/gorsel/([a-z0-9-]{1,40})\.png$")
KOSU_ADI = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{4}\.md$")
MALIYET = re.compile(r"maliyet:\s*([0-9.]+)\s*USD")
BEKCI_KARARI = re.compile(r"karar:\s*\*\*(\w+)\*\*")
GOVDE_SINIRI = 8 * 1024
DOSYALAR = {"/": ("index.html", "text/html; charset=utf-8"),
            "/robotlar.png": (KOK / "docs" / "4-ajan.png", "image/png")}


# --- veri --------------------------------------------------------------------------

def _oku(yol):
    try:
        return Path(yol).read_text(encoding="utf-8")
    except OSError:
        return ""


def _kosu_ozeti(takim, yol):
    metin = _oku(yol)
    maliyet = MALIYET.search(metin)
    karar = BEKCI_KARARI.findall(metin)
    if "**Atlandı:**" in metin:
        sonuc = "atlandi"
    elif "hata: True" in metin:
        sonuc = "hata"
    elif karar:
        sonuc = "red" if karar[-1] == "red" else "tamam"
    else:
        sonuc = "?"
    zaman = datetime.strptime(yol.stem, "%Y-%m-%d-%H%M")
    return {"takim": takim, "dosya": yol.name, "zaman": zaman.strftime("%Y-%m-%dT%H:%M"),
            "sonuc": sonuc, "maliyet": float(maliyet.group(1)) if maliyet else 0.0,
            "bekci": karar[-1] if karar else None}


def kosular(kok=KOK, sinir=30):
    tum = []
    for takim in ofis.takimlar(kok):
        for yol in (Path(kok) / "takimlar" / takim / "kosu").glob("*.md"):
            if KOSU_ADI.match(yol.name):
                tum.append(_kosu_ozeti(takim, yol))
    return sorted(tum, key=lambda k: k["zaman"], reverse=True)[:sinir]


def _defter_son_ders(kok, takim):
    metin = _oku(Path(kok) / "takimlar" / takim / "defter.md")
    bolum = metin.split("## Dersler", 1)[-1].split("\n## ", 1)[0]
    for satir in bolum.splitlines():
        satir = satir.strip().lstrip("-*").strip()
        if satir:
            return satir[:200]
    return None


def _ciktilar(kok, takim, sinir=3):
    klasor = Path(kok) / "takimlar" / takim / "cikti"
    if not klasor.is_dir():
        return []
    ogeler = sorted(klasor.iterdir(), key=lambda y: y.stat().st_mtime, reverse=True)
    return [str(y.relative_to(kok)) for y in ogeler if not y.name.startswith(".")][:sinir]


def _gelen_sayisi(kok):
    return len(list((Path(kok) / "takimlar" / "x-icerik" / "gelen").glob("*.json")))


def durum(kok=KOK, simdi=None):
    """Sayfanın tek veri kaynağı."""
    simdi = simdi or datetime.now().astimezone()
    tum_kosular = kosular(kok, sinir=200)
    bugun = simdi.strftime("%Y-%m-%d")
    uc_saat = (simdi - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M")
    son3 = [k for k in tum_kosular if k["zaman"] >= uc_saat]
    takim_verisi = {}
    for takim in ofis.takimlar(kok):
        d = ayar.durum_oku(takim, kok)
        takim_verisi[takim] = {
            "kuyruk": [o for o in (d.get("kuyruk") or []) if isinstance(o, dict)][-12:],
            "son_kosu": d.get("son_kosu"), "son_sonuc": d.get("son_sonuc"),
            "bekci": d.get("bekci") or {}, "defter": _defter_son_ders(kok, takim),
            "ciktilar": _ciktilar(kok, takim),
        }
    return {
        "sirket": ofis.SIRKET,
        "saat": simdi.strftime("%H:%M"),
        "mesai": {"icinde": ayar.mesaide_mi(simdi), "metin": ayar.MESAI_METNI,
                  "sonraki": ayar.sonraki_mesai(simdi).strftime("%a %H:%M")},
        "para": {"bugun": round(sum(k["maliyet"] for k in tum_kosular if k["zaman"].startswith(bugun)), 3),
                 "tavan": ayar.GUNLUK_MALIYET_TAVANI_USD},
        "gelen": _gelen_sayisi(kok),
        "gorseller": gorseller(),
        "ajanlar": ofis.besleme(kok)["agents"],
        "takimlar": takim_verisi,
        "kosular": tum_kosular[:30],
        "son3saat": {"kosu": len(son3), "tamam": sum(k["sonuc"] == "tamam" for k in son3),
                     "red": sum(k["sonuc"] == "red" for k in son3),
                     "atlandi": sum(k["sonuc"] == "atlandi" for k in son3),
                     "usd": round(sum(k["maliyet"] for k in son3), 3)},
        "icerik": ofis.icerik_acik(kok),
        "ekip": _ekip_verisi(kok),
        "ceo_raporlar": ceo_raporlari(kok),
    }


# --- ekip ve CEO ---------------------------------------------------------------------

CEO_KLASORU = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}$")
EKIP_KAYDI = re.compile(r"^sirket-log/ekip/\d{4}-\d{2}-\d{2}/\d{6}-[a-z0-9-]{1,40}\.md$")


def _ekip_verisi(kok):
    kayit = ofis.ekip_kaydi(kok)
    canli = ofis._canli()
    return {"ceo": kayit.get("ceo"), "aileler": kayit.get("aileler") or {}, "ajanlar": kayit.get("ajanlar") or [],
            "son": canli.get("ekip_son") or {}, "ceo_son": canli.get("ceo_son"),
            "ceo_simdi": canli.get("ceo")}


def ceo_raporlari(kok, sinir=10):
    klasor = Path(kok) / "sirket-log" / "ceo"
    if not klasor.is_dir():
        return []
    sonuc = []
    for k in sorted((y for y in klasor.iterdir() if CEO_KLASORU.match(y.name)), reverse=True)[:sinir]:
        is_ = _oku(k / "is.md").split("\n\n", 2)
        try:
            ozet = json.loads(_oku(k / "sonuc.json") or "{}")
        except ValueError:
            ozet = {}
        sonuc.append({"klasor": k.name, "is": (is_[1] if len(is_) > 1 else "")[:200],
                      "durum": ozet.get("durum") or ("sürüyor" if not (k / "rapor.md").exists() else "tamam"),
                      "maliyet": ozet.get("maliyet"), "rapor": (k / "rapor.md").is_file()})
    return sonuc


def ceo_raporu(kok, klasor):
    if not CEO_KLASORU.match(klasor or ""):
        return None
    k = Path(kok) / "sirket-log" / "ceo" / klasor
    if not k.is_dir():
        return None
    return _oku(k / "is.md") + "\n---\n\n" + (_oku(k / "rapor.md") or "(rapor henüz yok)")


def ekip_kaydi_metni(kok, yol):
    if not EKIP_KAYDI.match(yol or ""):
        return None
    dosya = Path(kok) / yol
    return _oku(dosya) if dosya.is_file() else None


def ceo_ver(kok, metin, yazabilir=False, cwd=None):
    """Patron Fable'a iş verir: bin/ceo.py arka planda başlar."""
    metin = str(metin or "").strip()[:4000]
    if not metin:
        return False, "iş metni boş"
    if (ofis._canli().get("ceo") or {}).get("basla") and any(
            a["id"] == "fable" and a["status"] == "running" for a in ofis.besleme(kok)["agents"]):
        return False, "Fable şu an başka bir işte"
    log = Path(kok) / "sirket-log"
    log.mkdir(exist_ok=True)
    k = [sys.executable, str(Path(kok) / "bin" / "ceo.py"), metin]
    if cwd:
        k += ["--cwd", str(cwd)]
    if yazabilir:
        k.append("--yazabilir")
    with open(log / "ofis-ceo.log", "a", encoding="utf-8") as cikis:
        subprocess.Popen(k, cwd=str(kok), stdout=cikis, stderr=subprocess.STDOUT, start_new_session=True)
    return True, "Fable işi aldı, ekibe dağıtıyor"


# Robot koleksiyonu (8 × 3 robot) ofis/gorseller/'e ya da bu reponun bir üst klasörüne bırakılabilir.
KOLEKSIYON = "robot-koleksiyonu"


def gorsel_yolu(ad):
    """Görselin dosyası; yalnız ofis/gorseller/ ve koleksiyon için bir üst klasör. Yoksa None."""
    for yol in (SAYFA / "gorseller" / f"{ad}.png",
                *( [KOK.parent / f"{KOLEKSIYON}.png"] if ad == KOLEKSIYON else [] )):
        if yol.is_file():
            return yol
    return None


def gorseller():
    adlar = {y.stem for y in (SAYFA / "gorseller").glob("*.png")}
    if gorsel_yolu(KOLEKSIYON):
        adlar.add(KOLEKSIYON)
    return sorted(adlar)


def kosu_metni(kok, takim, dosya):
    """Bir koşu kaydının metni; ad ve takım doğrulanır, başka dosya okunmaz."""
    if takim not in ofis.takimlar(kok) or not KOSU_ADI.match(dosya or ""):
        return None
    yol = Path(kok) / "takimlar" / takim / "kosu" / dosya
    return _oku(yol) if yol.is_file() else None


# --- eylemler ------------------------------------------------------------------------

def is_ver(kok, takim, metin, simdi=None):
    metin = re.sub(r"\s+", " ", str(metin or "")).strip()[:300]
    if takim not in ofis.takimlar(kok) or not metin:
        return False, "takım ya da iş metni geçersiz"
    id_ = "not-" + (simdi or datetime.now()).strftime("%Y%m%d%H%M%S")
    if not dagitici.kuyruga_yaz(kok, takim, id_, metin):
        return False, "kuyruğa yazılamadı"
    return True, id_


def kostur(kok, takim):
    if takim not in ofis.takimlar(kok):
        return False, "takım yok"
    if any(a["id"] == takim and a["status"] == "running" for a in ofis.besleme(kok)["agents"]):
        return False, "takım zaten koşuyor"
    log = Path(kok) / "sirket-log"
    log.mkdir(exist_ok=True)
    with open(log / "ofis-kos.log", "a", encoding="utf-8") as cikis:
        subprocess.Popen([sys.executable, str(Path(kok) / "bin" / "kos.py"), takim], cwd=str(kok),
                         stdout=cikis, stderr=subprocess.STDOUT, start_new_session=True)
    return True, "koşu başladı (mesai ve tavanlar geçerli)"


# --- http ----------------------------------------------------------------------------

class Isleyici(BaseHTTPRequestHandler):
    kok = KOK
    port = VARSAYILAN_PORT

    def log_message(self, *_):
        pass

    def _yanit(self, kod, govde, tur="application/json; charset=utf-8"):
        veri = govde if isinstance(govde, bytes) else json.dumps(govde, ensure_ascii=False).encode()
        self.send_response(kod)
        self.send_header("Content-Type", tur)
        self.send_header("Content-Length", str(len(veri)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(veri)

    def _kendimiz(self):
        return {f"127.0.0.1:{self.port}", f"localhost:{self.port}"}

    def _host_dogru(self):
        return self.headers.get("Host", "") in self._kendimiz()

    def do_GET(self):
        if not self._host_dogru():
            return self._yanit(403, {"hata": "host"})
        url = urlparse(self.path)
        if url.path == "/api/durum":
            return self._yanit(200, durum(self.kok))
        if url.path == "/api/ceo-rapor":
            metin = ceo_raporu(self.kok, (parse_qs(url.query).get("klasor") or [""])[0])
            return self._yanit(200, {"metin": metin}) if metin is not None else self._yanit(404, {"hata": "yok"})
        if url.path == "/api/ekip-kaydi":
            metin = ekip_kaydi_metni(self.kok, (parse_qs(url.query).get("yol") or [""])[0])
            return self._yanit(200, {"metin": metin}) if metin is not None else self._yanit(404, {"hata": "yok"})
        if url.path == "/api/kosu":
            q = parse_qs(url.query)
            metin = kosu_metni(self.kok, (q.get("takim") or [""])[0], (q.get("dosya") or [""])[0])
            return self._yanit(200, {"metin": metin}) if metin is not None else self._yanit(404, {"hata": "yok"})
        gorsel = GORSEL_ADI.match(url.path)
        if gorsel:
            yol = gorsel_yolu(gorsel.group(1))
            try:
                return self._yanit(200, yol.read_bytes(), "image/png") if yol else self._yanit(404, {"hata": "yok"})
            except OSError:
                return self._yanit(404, {"hata": "yok"})
        if url.path in DOSYALAR:
            ad, tur = DOSYALAR[url.path]
            yol = ad if isinstance(ad, Path) else SAYFA / ad
            try:
                return self._yanit(200, yol.read_bytes(), tur)
            except OSError:
                return self._yanit(404, {"hata": "yok"})
        return self._yanit(404, {"hata": "yok"})

    def do_POST(self):
        origin = self.headers.get("Origin", "")
        if (not self._host_dogru() or urlparse(origin).netloc not in self._kendimiz()
                or not self.headers.get("Content-Type", "").startswith("application/json")):
            return self._yanit(403, {"hata": "yalnız bu sayfadan"})
        uzunluk = int(self.headers.get("Content-Length") or 0)
        if uzunluk > GOVDE_SINIRI:
            return self._yanit(413, {"hata": "büyük"})
        try:
            veri = json.loads(self.rfile.read(uzunluk) or b"{}")
        except ValueError:
            return self._yanit(400, {"hata": "json"})
        takim = str(veri.get("takim") or "")
        yol = urlparse(self.path).path
        if yol == "/api/gordum" and takim == "fable":
            ofis.ceo_gordum(self.kok)
            tamam, mesaj = True, "rapor alındı"
        elif yol == "/api/gordum":
            if takim not in ofis.takimlar(self.kok):
                return self._yanit(400, {"hata": "takım yok"})
            ofis.gordum(takim, self.kok)
            tamam, mesaj = True, "el indi"
        elif yol == "/api/ceo":
            tamam, mesaj = ceo_ver(self.kok, veri.get("metin"), bool(veri.get("yazabilir")), veri.get("cwd"))
        elif yol == "/api/is":
            tamam, mesaj = is_ver(self.kok, takim, veri.get("metin"))
        elif yol == "/api/kos":
            tamam, mesaj = kostur(self.kok, takim)
        else:
            return self._yanit(404, {"hata": "yok"})
        return self._yanit(200 if tamam else 400, {"tamam": tamam, "mesaj": mesaj})


def sunucu(port=VARSAYILAN_PORT, kok=KOK):
    isleyici = type("Isleyici", (Isleyici,), {"kok": Path(kok), "port": port})
    return ThreadingHTTPServer(("127.0.0.1", port), isleyici)


def main(argv):
    port = int(argv[argv.index("--port") + 1]) if "--port" in argv else int(os.environ.get("OFIS_PORT") or VARSAYILAN_PORT)
    ofis.yaz()
    sv = sunucu(port)
    print(f"{ofis.SIRKET} ofisi: http://127.0.0.1:{port}")
    try:
        sv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
