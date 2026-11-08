#!/usr/bin/env python3
"""Günlük tetik — sabah ajanları başlatır ve rapor yazar, akşam günü denetler. LLM çağırmaz.

Kullanım:
  python3 bin/gunluk.py --sabah        # dağıtıcıyı koştur + sabah raporu yaz
  python3 bin/gunluk.py --aksam        # denetim raporu yaz (hiçbir şey koşturmaz)
  python3 bin/gunluk.py --sabah --kuru # hiçbir takımı başlatma, raporu ekrana bas

Rapor `sirket-log/rapor/YYYY-MM-DD-{sabah,aksam}.md` dosyasına yazılır. Dışarı hiçbir şey gitmez —
yayın düğmesi insanda. Zamanlayıcıyı `bin/zamanla.py` kurar.

ANAYASA §4 tek yerde: saatler ve tavanlar `bin/ayar.py`'de, koşma kararı `dagitici`'de.
Rapor yalnızca okur: `takimlar/*/kosu/*.md`, `takimlar/*/durum.json`, `takimlar/bekci-telemetri.jsonl`.
"""
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402
import dagitici  # noqa: E402

KOK = ayar.KOK
RAPOR_DIZINI = "sirket-log/rapor"
TELEMETRI = "takimlar/bekci-telemetri.jsonl"
GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]

# Haftalık iş — sabah tetiği bu maddeyi kuyruğa düşürmezse dağıtıcı o takımı hiç başlatmaz.
# `gun`: haftanın günü (0 = pazartesi). Hafta kimliği `youtube_analiz_cek.hafta_dosyasi` ile aynı.
HAFTALIK = [{"takim": "youtube-analiz", "gun": 0, "id": "yt-{hafta}",
             "not": "haftalık kanal raporu — son 7 gün"}]

KOSU_ADI = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d{2})(\d{2})\.md$")
OZET_SATIRI = re.compile(r"^- maliyet:\s*([\d.]+)\s*USD\s*·\s*tur:\s*(\d+)\s*·\s*hata:\s*(\w+)", re.M)
BEKCI_KARARI = re.compile(r"^## Bekçi\s*\n- karar:\s*\*\*(\w+)\*\*", re.M)
ATLANDI = re.compile(r"^\*\*Atlandı:\*\*\s*(.+)$", re.M)


# --- okuma -----------------------------------------------------------------

def kosu_oku(yol):
    """Bir koşu kaydını sözlüğe çevirir: saat, maliyet, hata, bekçi kararı, atlanma sebebi."""
    ad = KOSU_ADI.match(Path(yol).name)
    metin = Path(yol).read_text(encoding="utf-8", errors="ignore")
    ozet = OZET_SATIRI.search(metin)
    bekci = BEKCI_KARARI.search(metin)
    atlandi = ATLANDI.search(metin)
    return {"dosya": Path(yol).name,
            "gun": ad.group(1) if ad else "",
            "saat": f"{ad.group(2)}:{ad.group(3)}" if ad else "--:--",
            "maliyet": float(ozet.group(1)) if ozet else 0.0,
            "tur": int(ozet.group(2)) if ozet else 0,
            "hata": bool(ozet) and ozet.group(3) == "True",
            "bekci": bekci.group(1) if bekci else "-",
            "atlandi": atlandi.group(1).strip() if atlandi else None}


def gunun_kosulari(kok, gun):
    """O güne ait bütün koşu kayıtları, saate göre sıralı; her birine takım adı eklenir."""
    kosular = []
    for yol in sorted((Path(kok) / "takimlar").glob(f"*/kosu/{gun}-*.md")):
        if KOSU_ADI.match(yol.name):
            kosular.append({**kosu_oku(yol), "takim": yol.parent.parent.name})
    return sorted(kosular, key=lambda k: k["saat"])


def gunun_bekci_kararlari(kok, gun):
    """`bekci-telemetri.jsonl`'den o güne ait kararlar. Bozuk satır atlanır."""
    yol = Path(kok) / TELEMETRI
    if not yol.is_file():
        return []
    kararlar = []
    for satir in yol.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            kayit = json.loads(satir)
        except ValueError:
            continue
        if str(kayit.get("zaman", "")).startswith(gun):
            kararlar.append(kayit)
    return kararlar


def hafta_kimligi(simdi):
    """ISO hafta: `YYYY-Www` — `bin/youtube_analiz_cek.py`'nin veri dosyası adıyla birebir aynı."""
    yil, hafta, _ = simdi.isocalendar()
    return f"{yil}-W{hafta:02d}"


def haftalik_kuyruk(kok, simdi, kuru=False):
    """Haftanın gününe düşen işleri kuyruğa yazar. Aynı haftanın maddesi ikinci kez yazılmaz."""
    yazilan = []
    for madde in HAFTALIK:
        if simdi.weekday() != madde["gun"]:
            continue
        id_ = madde["id"].format(hafta=hafta_kimligi(simdi))
        varsa = any(o.get("id") == id_ for o in ayar.durum_oku(madde["takim"], kok).get("kuyruk") or []
                    if isinstance(o, dict))
        if varsa:
            continue
        if kuru or dagitici.kuyruga_yaz(kok, madde["takim"], id_, madde["not"]):
            yazilan.append({"takim": madde["takim"], "id": id_, "not": madde["not"]})
    return yazilan


def takim_ozeti(kok, takim, gun):
    durum = ayar.durum_oku(takim, kok)
    return {"takim": takim,
            "son_kosu": str(durum.get("son_kosu") or "-")[:16].replace("T", " "),
            "son_sonuc": durum.get("son_sonuc") or "-",
            "bekleyen": dagitici.bekleyen_sayisi(durum),
            "bugun": dagitici.bugunku_kosu_sayisi(kok, takim, gun),
            "bekci": (durum.get("bekci") or {}).get("son_karar") or "-"}


# --- yazma -----------------------------------------------------------------

def _baslik(tur, simdi):
    return f"# {tur} — {simdi:%Y-%m-%d} {GUNLER[simdi.weekday()]} {simdi:%H:%M}\n"


def _tablo(basliklar, satirlar):
    if not satirlar:
        return "(kayıt yok)\n"
    ust = "| " + " | ".join(basliklar) + " |\n| " + " | ".join("---" for _ in basliklar) + " |\n"
    return ust + "".join("| " + " | ".join(str(h) for h in s) + " |\n" for s in satirlar)


def _tavan_bolumu(kok, gun, takimlar):
    maliyet = dagitici.gunluk_maliyet(kok, gun)
    paylar = " · ".join(f"{t['takim']} {t['bugun']}/{ayar.GUNLUK_KOSU_TAVANI}" for t in takimlar)
    return (f"\n## Tavanlar (ANAYASA §4)\n"
            f"- gün toplamı: **{maliyet:.2f} / {ayar.GUNLUK_MALIYET_TAVANI_USD:.0f} USD**\n"
            f"- koşu sayısı: {paylar or '(takım yok)'}\n"
            f"- mesai {ayar.MESAI_METNI} · koşu başına {ayar.KOSU_BUTCESI_USD} USD / "
            f"{ayar.KOSU_SURESI_SN // 60} dk · iki koşu arası {ayar.KOSULAR_ARASI_DK} dk\n")


def sabah_raporu(kok, simdi, dagitim, haftalik=()):
    """Haftalık iş kuyruğa düştü mü, dağıtıcı ne başlattı, takımlar nerede, dün ne oldu."""
    gun = simdi.strftime("%Y-%m-%d")
    dun = (simdi - timedelta(days=1)).strftime("%Y-%m-%d")
    ozetler = [takim_ozeti(kok, t, gun) for t in dagitici.takimlar(kok)]
    dunku = gunun_kosulari(kok, dun)
    zincir = [f"- `{z['kaynak_takim']}/{z['kaynak_id']}` → `{z['takim']}/{z['id']}` ({z['ad']})"
              for z in dagitim.get("zincir") or []]
    haftalik_satirlari = [f"- `{h['takim']}` kuyruğuna `{h['id']}` düştü — {h['not']}" for h in haftalik]
    return (_baslik("Sabah raporu", simdi)
            + "\n## Haftalık iş\n"
            + ("".join(s + "\n" for s in haftalik_satirlari)
               or f"- bugün ({GUNLER[simdi.weekday()]}) haftalık iş yok\n")
            + "\n## Dağıtıcı ne yaptı\n" + ("".join(s + "\n" for s in zincir) or "- yeni zincir bağlantısı yok\n")
            + "\n" + _tablo(["Takım", "Karar", "Sebep"],
                     [[k["takim"], dagitici.ETIKET[k["sonuc"]].strip(), k["sebep"]]
                      for k in dagitim.get("kararlar") or []])
            + "\n## Takımlar\n"
            + _tablo(["Takım", "Son koşu", "Sonuç", "Bekleyen", "Bugün", "Bekçi"],
                     [[o["takim"], o["son_kosu"], o["son_sonuc"], o["bekleyen"], o["bugun"], o["bekci"]]
                      for o in ozetler])
            + f"\n## Dün ({dun})\n"
            + f"- {len(dunku)} koşu · {sum(k['maliyet'] for k in dunku):.2f} USD · "
              f"{sum(1 for k in dunku if k['bekci'] == 'red')} red · "
              f"{sum(1 for k in dunku if k['hata'])} hata\n"
            + _tavan_bolumu(kok, gun, ozetler))


def _dikkat_satirlari(kosular, kararlar):
    """Gözden kaçmaması gerekenler. Hiçbir şey yoksa boş liste — uydurma uyarı yok."""
    satirlar = []
    for kosu in kosular:
        if kosu["bekci"] == "red":
            satirlar.append(f"- ⛔ `{kosu['takim']}` {kosu['saat']} — bekçi **red**")
        elif kosu["hata"]:
            satirlar.append(f"- ⛔ `{kosu['takim']}` {kosu['saat']} — koşu hata ile bitti")
        elif kosu["atlandi"]:
            satirlar.append(f"- 🟡 `{kosu['takim']}` {kosu['saat']} — atlandı: {kosu['atlandi']}")
        elif kosu["bekci"] == "-":
            satirlar.append(f"- 🟡 `{kosu['takim']}` {kosu['saat']} — bekçi kararı kayda düşmemiş")
    for karar in kararlar:
        if karar.get("karar") == "atlandi":
            satirlar.append(f"- 🟡 `{karar.get('takim')}` — bekçi denetleyemedi: {karar.get('gerekce', '')[:120]}")
    return satirlar


def aksam_raporu(kok, simdi):
    """Günün koşuları + bekçi kararları. Hiçbir şey koşturmaz, yalnızca okur."""
    gun = simdi.strftime("%Y-%m-%d")
    kosular = gunun_kosulari(kok, gun)
    kararlar = gunun_bekci_kararlari(kok, gun)
    sayim = {d: sum(1 for k in kararlar if k.get("karar") == d) for d in ("kabul", "red", "atlandi")}
    dikkat = _dikkat_satirlari(kosular, kararlar)
    return (_baslik("Akşam denetimi", simdi)
            + f"\n## Bugünün koşuları ({len(kosular)})\n"
            + _tablo(["Saat", "Takım", "Maliyet", "Tur", "Hata", "Bekçi", "Not"],
                     [[k["saat"], k["takim"], f"{k['maliyet']:.3f}", k["tur"], "evet" if k["hata"] else "-",
                       k["bekci"], k["atlandi"] or "-"] for k in kosular])
            + f"\n## Bekçi kararları ({len(kararlar)})\n"
            + f"- kabul {sayim['kabul']} · **red {sayim['red']}** · atlandı {sayim['atlandi']}\n\n"
            + _tablo(["Saat", "Takım", "Karar", "İhlal", "Gerekçe"],
                     [[str(k.get("zaman", ""))[11:16], k.get("takim", "-"), k.get("karar", "-"),
                       k.get("ihlal_edilen_kural") or "-",
                       " ".join(str(k.get("gerekce") or "").split())[:120]] for k in kararlar])
            + "\n## Dikkat\n" + ("".join(s + "\n" for s in dikkat) or "- temiz gün, işaretlenecek bir şey yok\n")
            + _tavan_bolumu(kok, gun, [takim_ozeti(kok, t, gun) for t in dagitici.takimlar(kok)]))


def rapor_yolu(kok, tur, simdi):
    return Path(kok) / RAPOR_DIZINI / f"{simdi:%Y-%m-%d}-{tur}.md"


def yaz(kok, tur, metin, simdi):
    yol = rapor_yolu(kok, tur, simdi)
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(metin, encoding="utf-8")
    return yol


def sabah(kok, simdi=None, kuru=False):
    """Önce haftalık işi kuyruğa yaz, sonra dağıt — aynı sabah içinde tetiklensin."""
    simdi = simdi or datetime.now().astimezone()
    haftalik = haftalik_kuyruk(kok, simdi, kuru=kuru)
    dagitim = dagitici.dagit(kok, simdi, kuru=kuru)
    return sabah_raporu(kok, simdi, dagitim, haftalik), simdi


def aksam(kok, simdi=None):
    simdi = simdi or datetime.now().astimezone()
    return aksam_raporu(kok, simdi), simdi


def main(argv):
    kuru = "--kuru" in argv
    if "--sabah" in argv:
        tur, (metin, simdi) = "sabah", sabah(KOK, kuru=kuru)
    elif "--aksam" in argv:
        tur, (metin, simdi) = "aksam", aksam(KOK)
    else:
        print(__doc__)
        return 2
    if kuru:
        print(metin)
        print("(kuru koşu: rapor dosyaya yazılmadı, hiçbir takım başlatılmadı)")
        return 0
    print(f"rapor: {yaz(KOK, tur, metin, simdi).relative_to(KOK)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
