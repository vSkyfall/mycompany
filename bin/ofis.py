#!/usr/bin/env python3
"""Ofis beslemesi — şirketi (mycompany) Cubicle'ın piksel ofisinde gösterir.

Cubicle (https://github.com/caglarutkuguler/cubicle) bir JSON beslemesini okur ve her kaydı ofiste
bir çalışan olarak çizer. Bu modül o beslemeyi yazar: her takım bir çalışan, bekçi ayrı bir çalışan.

Durum iki yerden gelir:
  - kalıcı: `takimlar/<takim>/durum.json` (son sonuç, kuyruk, bekçi kararı)
  - canlı:  `~/.cubicle/a-sirketi.canli.json` (şu an koşan takım, denetleyen bekçi, son araç adımları)

Ofiste ne görünür:
  koşuyor            → masada, yazıyor; balonda kuyruktaki iş
  tamam (son halka)  → el kaldırır: "hazır — yayın düğmesi sende"   (ANAYASA §1)
  tamam (zincir)     → molaya gider, "✓ bitti"; iş dağıtıcıyla sonraki takıma geçer
  red / hata         → masaya yığılır, kartta bekçinin gerekçesi
  atlandı            → "zZ" (mesai dışı, tavan, eksik anahtar)

Ofis bir göstergedir; şirketin işine asla engel olmaz. Buradaki hiçbir çağrı hata fırlatmaz,
`OFIS_KAPALI=1` beslemeyi tamamen kapatır. Besleme yalnız gerçek repo kökü için yazılır
(testlerin geçici kökleri ofise düşmez); `OFIS_BESLEME` yolu değiştirir.

Kullanım:
  python3 bin/ofis.py                  # beslemeyi durum dosyalarından yeniden yaz, özet bas
  python3 bin/ofis.py --gordum <takim> # "yayın sende" elini indir (paketi aldın)
  python3 bin/ofis.py --hook           # claude -p kancası (PreToolUse/PostToolUse); kos.py bağlar
"""
import fcntl
import json
import os
import re
import sys
import time
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402

# Ofiste görünen şirket adı; OFIS_SIRKET_ADI ile değişir.
SIRKET = os.environ.get("OFIS_SIRKET_ADI") or "mycompany"
TAZE_SN = ayar.KOSU_SURESI_SN + 300   # canlı kayıt bundan eskiyse koşu çökmüş say
ADIM_SAYISI = 10
BEKCI = "bekci"
GORUNUM_PORT = 3210   # bin/ofis_sunucu.py — şirketin kendi ofis görünümü
# Gerçek repo kökü, bu dosyanın yerinden: testler ayar.KOK'u geçici köke çevirse de ofise yazılmaz.
GERCEK_KOK = Path(__file__).resolve().parents[1]


def besleme_yolu():
    return Path(os.environ.get("OFIS_BESLEME") or Path.home() / ".cubicle" / "a-sirketi.json")


def _canli_yolu():
    yol = besleme_yolu()
    return yol.with_name(yol.stem + ".canli.json")


def _acik(kok=None):
    if os.environ.get("OFIS_KAPALI", "").lower() in ("1", "true", "evet", "yes"):
        return False
    if os.environ.get("OFIS_BESLEME"):
        return True
    return Path(kok or ayar.KOK).resolve() == GERCEK_KOK


def _ms():
    return int(time.time() * 1000)


@contextmanager
def _kilit():
    yol = besleme_yolu()
    yol.parent.mkdir(parents=True, exist_ok=True)
    with open(yol.with_name(yol.stem + ".lock"), "w") as kilit:
        fcntl.flock(kilit, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(kilit, fcntl.LOCK_UN)


def _oku_json(yol, varsayilan):
    try:
        veri = json.loads(Path(yol).read_text(encoding="utf-8"))
        return veri if isinstance(veri, type(varsayilan)) else varsayilan
    except (OSError, ValueError):
        return varsayilan


def _yaz_json(yol, veri):
    yol = Path(yol)
    gecici = yol.with_name(f"{yol.name}.{os.getpid()}.tmp")
    gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(gecici, yol)   # okuyan hiçbir zaman yarım dosya görmez


def _canli():
    veri = _oku_json(_canli_yolu(), {})
    for alan in ("kosan", "adimlar", "son_is", "gordum", "ekip", "ekip_son"):
        veri.setdefault(alan, {})
    veri.setdefault("bekci", None)
    veri.setdefault("ceo", None)
    veri.setdefault("ceo_son", None)
    veri.setdefault("ceo_isler", {})
    return veri


# --- takımlar ve kuyruk -----------------------------------------------------

def takimlar(kok=None):
    kok = Path(kok or ayar.KOK)
    return sorted(y.parent.name for y in (kok / "takimlar").glob("*/takim.md")
                  if not y.parent.name.startswith("_"))


def _zincire_verenler():
    """İşini dağıtıcıya devreden takımlar (çıktısı yayına değil, sonraki takıma gider)."""
    try:
        import dagitici
        import telegram_dinle
    except Exception:
        return {"x-icerik"}
    return {t for t, onek in telegram_dinle.KUYRUK_ONEKI.items()
            if any(z["desen"].match(f"{onek}-1") for z in dagitici.ZINCIR)}


def _bekleyenler(durum):
    return [o for o in (durum.get("kuyruk") or [])
            if isinstance(o, dict) and o.get("durum") == "bekliyor"]


def siradaki_is(takim, kok=None):
    """Takımın kuyruğunda sıradaki bekleyen madde → {"id", "title"}; yoksa None."""
    bekleyen = _bekleyenler(ayar.durum_oku(takim, kok))
    if not bekleyen:
        return None
    ilk = bekleyen[0]
    return {"id": str(ilk.get("id") or ""), "title": str(ilk.get("not") or "kuyruktaki iş")[:120]}


def _atlanma_sebebi(takim, kok):
    kosular = sorted((Path(kok or ayar.KOK) / "takimlar" / takim / "kosu").glob("*.md"))
    if not kosular:
        return "atlandı"
    try:
        eslesme = re.search(r"\*\*Atlandı:\*\*\s*(.+)", kosular[-1].read_text(encoding="utf-8"))
    except OSError:
        return "atlandı"
    return eslesme.group(1).strip()[:120] if eslesme else "atlandı"


def _rol(fm):
    metin = str((fm or {}).get("description") or "").strip()
    metin = re.sub(r"\s+", " ", metin)
    return metin if len(metin) <= 70 else metin[:69] + "…"


def _taze(kayit):
    return isinstance(kayit, dict) and _ms() - int(kayit.get("basla", 0)) < TAZE_SN * 1000


# --- besleme ------------------------------------------------------------------

def _takim_ajani(takim, sira, canli, verenler, kok):
    fm = ayar.takim_bilgisi(takim, kok) or {}
    durum = ayar.durum_oku(takim, kok)
    ajan = {"id": takim, "name": takim, "role": _rol(fm), "since": sira, "status": "idle",
            "completedAt": None}
    adimlar = canli["adimlar"].get(takim)
    if adimlar:
        ajan["recent"] = adimlar[-ADIM_SAYISI:]
    sonuc, son_kosu = durum.get("son_sonuc"), durum.get("son_kosu")
    son_is = canli["son_is"].get(takim) or {}
    if sonuc == "tamam":
        ajan["completedAt"] = son_kosu
    bekleyen = _bekleyenler(durum)
    kosan = canli["kosan"].get(takim)
    if _taze(kosan):
        ajan.update(status="running", task=kosan.get("is") or {"id": "", "title": "koşu"})
    elif sonuc == "tamam" and takim not in verenler and canli["gordum"].get(takim) != son_kosu:
        baslik = (son_is.get("title") + " — " if son_is.get("title") else "") + "hazır, yayın düğmesi sende"
        ajan.update(status="waiting", task={"id": son_is.get("id", ""), "title": baslik})
    elif sonuc in ("red", "hata"):
        gerekce = (durum.get("bekci") or {}).get("gerekce") if sonuc == "red" else ""
        ajan.update(status="error", error=("bekçi red: " + gerekce) if gerekce else
                    ("bekçi red" if sonuc == "red" else "koşu hatası — koşu kaydına bak"))
    elif sonuc == "atlandi":
        ajan.update(status="paused", task=_atlanma_sebebi(takim, kok))
    if ajan["status"] in ("idle", "paused") and bekleyen and "task" not in ajan:
        ajan["task"] = f"kuyrukta {len(bekleyen)} iş · sıradaki {bekleyen[0].get('id')}"
    return ajan


def _bekci_ajani(sira, canli, kok):
    anahtar = (os.environ.get("OPENAI_API_KEY") or ayar.env_yukle().get("OPENAI_API_KEY") or "").strip()
    ajan = {"id": BEKCI, "name": "Bekçi", "since": sira, "status": "idle",
            "role": "Denetçi · ayrı model (OpenAI)" if anahtar else "Denetçi · yedek: Claude Haiku"}
    denetim = canli.get("bekci")
    if _taze(denetim):
        ajan.update(status="running", task=f"{denetim.get('takim')} koşusunu denetliyor",
                    parent=denetim.get("takim"))
        return ajan
    kararlar = [(b.get("zaman") or "", t, b) for t in takimlar(kok)
                for b in [ayar.durum_oku(t, kok).get("bekci") or {}] if b.get("son_karar")]
    if kararlar:
        _, takim, b = max(kararlar)
        ajan["task"] = f"son karar: {b['son_karar']} — {takim}"
    return ajan


EKIP_TAZE_SN = 1800        # bir ajan işi en fazla bu kadar sürer; daha eski "çalışıyor" kaydı çökmüştür
EKIP_YENI_SN = 300         # biten iş bu süre boyunca kartta "✓ bitti" diye görünür


def ekip_kaydi(kok=None):
    """sirket/ekip.json; yoksa ya da bozuksa boş ekip."""
    return _oku_json(Path(kok or ayar.KOK) / "sirket" / "ekip.json", {}) or {}


def _kisa(metin, n=110):
    metin = re.sub(r"\s+", " ", str(metin or "")).strip()
    return metin if len(metin) <= n else metin[:n - 1] + "…"


def _ekip_ajanlari(sira, canli, kok):
    """CEO (Fable) ve ekibi: her biri bir masa. CEO raporu hazırsa patronu bekler."""
    kayit = ekip_kaydi(kok)
    if not kayit.get("ceo"):
        return []
    aileler = kayit.get("aileler") or {}
    ceo = kayit["ceo"]
    # Cubicle'da CEO sıraların önündeki kendi masasında, ekip de boştayken masasında oturur.
    ajan = {"id": ceo["id"], "name": ceo["ad"], "role": f"CEO · {ceo['model']}", "since": sira,
            "status": "idle", "completedAt": None, "desk": "front", "stay": True}
    adimlar = canli["adimlar"].get(ceo["id"])
    if adimlar:
        ajan["recent"] = adimlar[-ADIM_SAYISI:]
    simdi, son = canli.get("ceo"), canli.get("ceo_son")
    if isinstance(simdi, dict) and _ms() - int(simdi.get("basla", 0)) < EKIP_TAZE_SN * 1000:
        ajan.update(status="running", task=_kisa(simdi.get("is"), 80))
    elif isinstance(son, dict) and not son.get("gordum"):
        if son.get("durum") == "tamam":
            ajan.update(status="waiting", task=f"rapor hazır: {_kisa(son.get('is'), 60)}")
        else:
            ajan.update(status="error", error=f"CEO işi bitmedi: {_kisa(son.get('neden') or son.get('durum'), 80)}")
    ajanlar = [ajan]
    for i, a in enumerate(kayit.get("ajanlar") or []):
        aile = (aileler.get(a["aile"]) or {}).get("ad", a["aile"])
        x = {"id": a["id"], "name": f"{a['ad']} · {aile}", "role": a["rol"], "since": sira + 1 + i,
             "status": "idle", "parent": ceo["id"], "stay": True}
        su_an, son_is = canli["ekip"].get(a["id"]), canli["ekip_son"].get(a["id"])
        if isinstance(su_an, dict) and _ms() - int(su_an.get("basla", 0)) < EKIP_TAZE_SN * 1000:
            x.update(status="running", task=_kisa(su_an.get("is"), 80))
        elif isinstance(son_is, dict):
            if son_is.get("durum") != "tamam" and _ms() - int(son_is.get("bitti", 0)) < EKIP_YENI_SN * 1000:
                x.update(status="error", error=f"{son_is.get('durum')}: {_kisa(son_is.get('ozet'), 80)}")
            else:
                x["task"] = f"son iş: {_kisa(son_is.get('is'), 70)}"
                if son_is.get("durum") == "tamam":
                    x["completedAt"] = son_is.get("bitti")
        ajanlar.append(x)
    return ajanlar


def icerik_acik(kok=None):
    """sirket/ofis.json'daki icerik_takimlari; dosya yoksa açık (eski davranış)."""
    ayarlar = _oku_json(Path(kok or ayar.KOK) / "sirket" / "ofis.json", {})
    return bool(ayarlar.get("icerik_takimlari", True))


def besleme(kok=None, canli=None):
    """Cubicle besleme sözlüğü (cubicle/docs/FEED.md biçimi)."""
    canli = canli if canli is not None else _canli()
    ajanlar = []
    if icerik_acik(kok):   # API anahtarı isteyen içerik köyü; kapalıyken ofiste görünmez
        verenler = _zincire_verenler()
        ajanlar = [_takim_ajani(t, i, canli, verenler, kok) for i, t in enumerate(takimlar(kok))]
        ajanlar.append(_bekci_ajani(len(ajanlar), canli, kok))
    ajanlar.extend(_ekip_ajanlari(len(ajanlar), canli, kok))
    port = os.environ.get("OFIS_PORT") or GORUNUM_PORT
    # Cubicle menüsünde şirket seçilince piksel ofis yerine bu sayfa açılır.
    return {"company": SIRKET, "view": f"http://127.0.0.1:{port}/", "agents": ajanlar}


def _yaz(kok, canli):
    _yaz_json(besleme_yolu(), besleme(kok, canli))


def yaz(kok=None):
    """Beslemeyi durum dosyalarından yeniden yazar. Hata fırlatmaz; yazıldıysa True."""
    if not _acik(kok):
        return False
    try:
        with _kilit():
            _yaz(kok, _canli())
        return True
    except Exception:
        return False


def _guncelle(degistir, kok=None):
    """Canlı katmanı kilit altında değiştirir ve beslemeyi tazeler. Hata fırlatmaz."""
    if not _acik(kok):
        return
    try:
        with _kilit():
            canli = _canli()
            _yetimleri_topla(canli)
            degistir(canli)
            _yaz_json(_canli_yolu(), canli)
            _yaz(kok, canli)
    except Exception:
        pass


# --- olaylar --------------------------------------------------------------------

def basladi(takim, kok=None):
    """kos.py claude'u başlatmadan hemen önce çağırır."""
    is_ = siradaki_is(takim, kok) or {"id": "", "title": "koşu"}

    def degistir(canli):
        canli["kosan"][takim] = {"basla": _ms(), "is": is_}
        canli["adimlar"][takim] = []
        canli["son_is"][takim] = is_
        canli["gordum"].pop(takim, None)
    _guncelle(degistir, kok)


def bitti(takim, kok=None):
    """kos.py koşu bitince (başarılı ya da değil) çağırır."""
    def degistir(canli):
        canli["kosan"].pop(takim, None)
        for adim in canli["adimlar"].get(takim) or []:
            if len(adim) == 2:                     # bitişi gelmemiş adım: koşuyla birlikte kapanır
                adim.append(max(0, _ms() - adim[0]))
    _guncelle(degistir, kok)


def bekci_basladi(takim, kok=None):
    def degistir(canli):
        canli["bekci"] = {"basla": _ms(), "takim": takim}
    _guncelle(degistir, kok)


def bekci_bitti(kok=None):
    def degistir(canli):
        canli["bekci"] = None
    _guncelle(degistir, kok)


def gordum(takim, kok=None):
    """İnsan paketi aldı: "yayın sende" eli iner (bir sonraki koşuya kadar)."""
    son_kosu = ayar.durum_oku(takim, kok).get("son_kosu")

    def degistir(canli):
        canli["gordum"][takim] = son_kosu
    _guncelle(degistir, kok)


def ekip_basladi(ajan_id, is_, kok=None):
    def degistir(canli):
        canli["ekip"][ajan_id] = {"basla": _ms(), "is": _kisa(is_, 200), "pid": os.getpid()}
    _guncelle(degistir, kok)


def _yasiyor(pid):
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except (PermissionError, ValueError, OverflowError, TypeError):
        return True
    return True


def _yetimleri_topla(canli):
    """Süreci ölmüş "çalışıyor" kayıtları kapatır: ekip.py dışarıdan öldürülünce (Claude Code'da Durdur)
    bitti diyemez, masa 30 dk yanık kalırdı."""
    for ajan_id, kayit in list(canli["ekip"].items()):
        pid = (kayit or {}).get("pid")
        if pid and not _yasiyor(pid):
            canli["ekip"].pop(ajan_id)
            canli["ekip_son"][ajan_id] = {"bitti": _ms(), "durum": "durduruldu", "is": kayit.get("is", ""),
                                          "ozet": "süreç dışarıdan durduruldu", "kayit": "",
                                          "sure": max(0, (_ms() - int(kayit.get("basla", _ms()))) // 1000)}


def ekip_bitti(ajan_id, durum, yanit, sure, kayit, kok=None):
    def degistir(canli):
        once = canli["ekip"].pop(ajan_id, None) or {}
        canli["ekip_son"][ajan_id] = {"bitti": _ms(), "durum": durum, "is": once.get("is", ""),
                                      "ozet": _kisa(yanit, 300), "sure": sure, "kayit": kayit}
    _guncelle(degistir, kok)


def _aktif_ceo_isleri(canli):
    """Süren CEO işleri, klasör → kayıt. Aynı anda birden çok Fable oturumu olabilir (Desktop'ta iki sohbet);
    her iş kendi klasörüyle ayrı tutulur ki birinin bitişi ötekini kapatmasın. Bayat kayıt (çökmüş oturum) düşer."""
    isler = canli.setdefault("ceo_isler", {})
    for k in [k for k, v in isler.items() if _ms() - int((v or {}).get("basla", 0)) >= EKIP_TAZE_SN * 1000]:
        del isler[k]
    return isler


def ceo_basladi(is_, klasor, kok=None, oturum=""):
    def degistir(canli):
        isler = _aktif_ceo_isleri(canli)
        if not isler:                       # masa boştu: adım listesi sıfırdan; başka iş sürüyorsa adımlar birikir
            canli["adimlar"]["fable"] = []
        kayit = {"basla": _ms(), "is": _kisa(is_, 300), "klasor": klasor, "oturum": oturum or ""}
        isler[klasor] = kayit
        canli["ceo"] = kayit                # masada en son başlayan iş görünür
    _guncelle(degistir, kok)


def ceo_bitti(durum, rapor, maliyet=None, neden="", kok=None, klasor=None):
    """`klasor` verilirse yalnız o iş kapanır; başka oturumun işi sürüyorsa masa dolu kalır."""
    def degistir(canli):
        isler = _aktif_ceo_isleri(canli)
        once = (isler.get(klasor) if klasor else canli.get("ceo")) or {"klasor": klasor}
        isler.pop(once.get("klasor"), None)
        canli["ceo"] = max(isler.values(), key=lambda k: k.get("basla", 0), default=None)
        canli["ceo_son"] = {"bitti": _ms(), "durum": durum, "is": once.get("is", ""), "klasor": once.get("klasor"),
                            "rapor": rapor, "maliyet": maliyet, "neden": _kisa(neden, 200), "gordum": False}
    _guncelle(degistir, kok)


def ceo_gordum(kok=None):
    """Patron CEO raporunu aldı: Fable'ın eli iner."""
    def degistir(canli):
        if isinstance(canli.get("ceo_son"), dict):
            canli["ceo_son"]["gordum"] = True
    _guncelle(degistir, kok)


# --- claude -p kancası ------------------------------------------------------------

def adim_ozeti(arac, girdi):
    girdi = girdi if isinstance(girdi, dict) else {}
    if arac == "Bash":
        ayrinti = girdi.get("command", "")
    elif arac in ("Read", "Write", "Edit", "MultiEdit"):
        ayrinti = Path(str(girdi.get("file_path", ""))).name
    elif arac in ("Glob", "Grep"):
        ayrinti = girdi.get("pattern", "")
    elif arac == "WebSearch":
        ayrinti = girdi.get("query", "")
    elif arac == "WebFetch":
        ayrinti = re.sub(r"^https?://", "", str(girdi.get("url", ""))).split("/")[0]
    else:
        ayrinti = ""
    ayrinti = re.sub(r"\s+", " ", str(ayrinti)).strip()
    if len(ayrinti) > 60:
        ayrinti = ayrinti[:59] + "…"
    return f"{arac}: {ayrinti}" if ayrinti else str(arac)


def kanca_isle(olay, takim, kok=None):
    """PreToolUse adımı açar, PostToolUse aynı adımı süresiyle kapatır."""
    ad = olay.get("hook_event_name")
    if ad not in ("PreToolUse", "PostToolUse"):
        return
    ozet = adim_ozeti(olay.get("tool_name") or "?", olay.get("tool_input"))

    def degistir(canli):
        adimlar = canli["adimlar"].setdefault(takim, [])
        if ad == "PreToolUse":
            adimlar.append([_ms(), ozet])
            del adimlar[:-ADIM_SAYISI]
            return
        for adim in reversed(adimlar):
            if len(adim) == 2 and adim[1] == ozet:
                adim.append(max(0, _ms() - adim[0]))
                return
    _guncelle(degistir, kok)


def kanca_ayari(kok=None):
    """kos.py'nin `claude -p --settings` ile verdiği ayar: yalnız şirket koşularında çalışır."""
    betik = Path(kok or ayar.KOK) / "bin" / "ofis.py"
    komut = f'python3 "{betik}" --hook'
    grup = [{"matcher": "", "hooks": [{"type": "command", "command": komut, "timeout": 5}]}]
    return json.dumps({"hooks": {"PreToolUse": grup, "PostToolUse": grup}})


def _kanca():
    # SIRKET_TAKIM: içerik takımı koşusu (kos.py) · OFIS_AJAN: CEO koşusu (ceo.py)
    takim = os.environ.get("SIRKET_TAKIM") or os.environ.get("OFIS_AJAN")
    try:
        olay = json.load(sys.stdin)
    except ValueError:
        return 0
    if takim and isinstance(olay, dict):
        kanca_isle(olay, takim)
    return 0   # stdout'a hiçbir şey yazılmaz: kanca ajanın kararına karışmaz


def main(argv):
    if "--hook" in argv:
        return _kanca()
    if "--gordum" in argv:
        i = argv.index("--gordum")
        if i + 1 >= len(argv) or argv[i + 1] not in takimlar():
            print("kullanım: python3 bin/ofis.py --gordum <takim>   (takımlar: "
                  + ", ".join(takimlar()) + ")")
            return 2
        gordum(argv[i + 1])
    if not yaz():
        print("ofis beslemesi yazılmadı (OFIS_KAPALI açık ya da yazma hatası)")
        return 1
    print(f"ofis beslemesi: {besleme_yolu()}")
    for ajan in besleme()["agents"]:
        is_ = ajan.get("task") or ajan.get("error") or ""
        if isinstance(is_, dict):
            is_ = " ".join(x for x in (is_.get("id"), is_.get("title")) if x)
        print(f"  {ajan['name']:<16} {ajan['status']:<8} {is_}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
