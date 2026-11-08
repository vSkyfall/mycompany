#!/usr/bin/env python3
"""Ekip dağıtıcısı — CEO'nun (Fable) ajanlara iş verdiği tek kapı.

Ekip `sirket/ekip.json`'da: her ajanın ailesi (claude / antigravity / codex), tam model adı ve rolü.
Bu betik doğru CLI'ı çağırır, işin sürdüğünü ofise yazar (ajanın masası yanar), yanıtı tek satır
JSON olarak basar ve brif + yanıtı `sirket-log/ekip/<gün>/` altına kaydeder.

  claude       → claude -p --model <model>            (salt-okunur: Read, Glob, Grep, WebSearch, WebFetch)
  antigravity  → ~/.claude/skills/delegate/scripts/delegate.sh --to agy --model <model>
  codex        → codex exec -s read-only [-m <model>]  (model null = hesaptaki varsayılan)

Varsayılan SALT-OKUNUR. `--yaz` yalnız MYCOMPANY_YAZMA=1 ortamında kabul edilir; bunu ceo.py, patron
"dosya değiştirebilir" dediğinde koyar. Gizli bilgi (.env, anahtar) brife girmez.

Kullanım:
  python3 bin/ekip.py liste
  python3 bin/ekip.py ver <ajan> --brif "görev metni" [--cwd KLASÖR] [--arastirma] [--yaz] [--sure SN]
  python3 bin/ekip.py ver <ajan> --brif-dosyasi brif.md [...]
"""
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402
import ofis  # noqa: E402

KOK = ayar.KOK
EKIP_DOSYASI = KOK / "sirket" / "ekip.json"
DELEGE = Path.home() / ".claude" / "skills" / "delegate" / "scripts" / "delegate.sh"
VARSAYILAN_SURE = 540   # CEO'nun Bash aracı en fazla 10 dk bekler; payıyla sığsın
# Para tavanı yok: abonelikte claude -p'nin USD sayacı tahminidir, gerçek fren kullanım penceresi ve süredir.
CLAUDE_BUTCESI_USD = None
YANIT_SINIRI = 20000


def ekip(yol=EKIP_DOSYASI):
    return json.loads(Path(yol).read_text(encoding="utf-8"))


def ajan_bul(ajan_id, veri=None):
    veri = veri or ekip()
    return next((a for a in veri["ajanlar"] if a["id"] == ajan_id), None)


def calisma_klasoru(ham):
    """İşçinin çalışacağı klasör: var olmalı ve ev klasörünün altında olmalı."""
    yol = Path(os.path.expanduser(ham or str(KOK.parent))).resolve()
    if not yol.is_dir() or Path.home().resolve() not in (yol, *yol.parents):
        raise ValueError(f"çalışma klasörü geçersiz: {ham}")
    return yol


# --- komutlar ------------------------------------------------------------------

def komut(ajan, brif, cwd, arastirma=False, yaz=False, sure=VARSAYILAN_SURE, son_dosya=None):
    """Ajan için çalıştırılacak komut (liste). Hiçbir şey çalıştırmaz."""
    aile, model = ajan["aile"], ajan.get("model")
    if aile == "claude":
        araclar = ["Read", "Glob", "Grep", "WebSearch", "WebFetch"] + (["Edit", "Write"] if yaz else [])
        k = ["claude", "-p", brif, "--output-format", "json",
             "--allowedTools", ",".join(araclar), "--setting-sources", "project,local"]
        if CLAUDE_BUTCESI_USD:
            k += ["--max-budget-usd", str(CLAUDE_BUTCESI_USD)]
        if model:
            k += ["--model", model]
        if yaz:
            k += ["--permission-mode", "acceptEdits"]
        return k
    if aile == "antigravity":
        if not yaz and not arastirma:
            # Salt-okunur agy izin isteyen her aracı reddeder ve boş döner (çıkış 77): baştan söyle.
            brif += "\n\n(Kabuk komutu çalıştırma, dosya yazma; dosyaları yerleşik okuma aracıyla oku.)"
        k = [str(DELEGE), "--to", "agy", "--model", model, "--cwd", str(cwd), "--timeout", str(sure)]
        if arastirma:
            k.append("--research")
        if yaz:
            k.append("--write")
        return k + [brif]
    if aile == "codex":
        k = ["codex", "exec", "--skip-git-repo-check", "-C", str(cwd),
             "-s", "workspace-write" if yaz else "read-only", "-o", str(son_dosya)]
        if model:
            k += ["-m", model]
        return k + [brif]
    raise ValueError(f"bilinmeyen aile: {aile}")


def _yaniti_coz(ajan, cikti, son_dosya):
    """CLI çıktısından (yanıt metni, ek bilgi) çıkarır."""
    aile = ajan["aile"]
    if aile == "claude":
        try:
            d = json.loads(cikti.stdout)
            return str(d.get("result") or ""), {"maliyet": d.get("total_cost_usd"), "hata": bool(d.get("is_error"))}
        except ValueError:
            return (cikti.stdout or cikti.stderr)[-YANIT_SINIRI:], {"hata": True}
    if aile == "antigravity":
        try:
            d = json.loads(cikti.stdout.strip().splitlines()[-1])
            sorun = d.get("exit") not in (0, None) or d.get("stalled") or d.get("denied") not in (None, False)
            return str(d.get("response") or ""), {"hata": bool(sorun), "exit": d.get("exit"),
                                                  "stalled": d.get("stalled"), "denied": d.get("denied")}
        except (ValueError, IndexError):
            return (cikti.stdout or cikti.stderr)[-YANIT_SINIRI:], {"hata": True}
    metin = ""
    try:
        metin = Path(son_dosya).read_text(encoding="utf-8")
    except OSError:
        pass
    return metin or (cikti.stderr or "")[-4000:], {"hata": cikti.returncode != 0 or not metin}


def _kaydet(ajan, brif, yanit, sonuc):
    gun = datetime.now().strftime("%Y-%m-%d")
    klasor = KOK / "sirket-log" / "ekip" / gun
    klasor.mkdir(parents=True, exist_ok=True)
    yol = klasor / f"{datetime.now():%H%M%S}-{ajan['id']}.md"
    yol.write_text(f"# {ajan['ad']} ({ajan['aile']} · {ajan.get('model') or 'varsayılan'})\n\n"
                   f"- durum: {sonuc['durum']} · süre: {sonuc['sure']} sn\n\n## Brif\n\n{brif}\n\n## Yanıt\n\n{yanit}\n",
                   encoding="utf-8")
    return str(yol.relative_to(KOK))


class Durduruldu(Exception):
    """Dışarıdan durdurma sinyali: patron Claude Code'da Durdur'a bastı ya da süreç kapatıldı."""


def _sinyal(_num, _frame):
    raise Durduruldu()


def sinyalleri_yakala():
    """SIGTERM/SIGINT/SIGHUP gelince ajan süreci kapanır ve ofise 'durduruldu' denir (yalnız komut satırında)."""
    for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(s, _sinyal)


def ver(ajan_id, brif, cwd=None, arastirma=False, yaz=False, sure=VARSAYILAN_SURE, calistir=subprocess.run):
    """Ajana işi verir, bitene kadar bekler, sonucu sözlük olarak döner."""
    veri = ekip()
    ajan = ajan_bul(ajan_id, veri)
    if not ajan:
        return {"ajan": ajan_id, "durum": "hata", "yanit": f"ekipte yok: {ajan_id}. Geçerli: "
                + ", ".join(a["id"] for a in veri["ajanlar"])}
    brif = str(brif or "").strip()
    if not brif:
        return {"ajan": ajan_id, "durum": "hata", "yanit": "brif boş"}
    if yaz and os.environ.get("MYCOMPANY_YAZMA") != "1":
        return {"ajan": ajan_id, "durum": "hata",
                "yanit": "yazma izni yok: patron bu iş için 'dosya değiştirebilir' demedi. Salt-okunur çalıştır."}
    try:
        klasor = calisma_klasoru(cwd)
    except ValueError as exc:
        return {"ajan": ajan_id, "durum": "hata", "yanit": str(exc)}
    son = tempfile.NamedTemporaryFile(prefix="ekip-", suffix=".txt", delete=False)
    son.close()
    k = komut(ajan, brif, klasor, arastirma, yaz, sure, son.name)
    ortam = {x: v for x, v in os.environ.items() if x not in ("CLAUDECODE", "SIRKET_TAKIM", "SIRKET_KOSU", "OFIS_AJAN")}
    ofis.ekip_basladi(ajan_id, brif)
    bas = time.time()
    try:
        cikti = calistir(k, cwd=str(klasor), capture_output=True, text=True, timeout=sure + 30, env=ortam,
                         stdin=subprocess.DEVNULL)
        yanit, ek = _yaniti_coz(ajan, cikti, son.name)
        durum = "hata" if ek.pop("hata", False) else "tamam"
    except subprocess.TimeoutExpired:
        yanit, ek, durum = f"{sure} sn içinde bitmedi", {}, "zaman_asimi"
    except Durduruldu:
        yanit, ek, durum = "patron durdurdu", {}, "durduruldu"     # subprocess.run alt süreci öldürüp yükseltir
    except OSError as exc:
        yanit, ek, durum = f"CLI başlatılamadı: {exc}", {}, "hata"
    finally:
        Path(son.name).unlink(missing_ok=True)
    sonuc = {"ajan": ajan_id, "model": ajan.get("model") or "varsayılan", "aile": ajan["aile"],
             "durum": durum, "sure": round(time.time() - bas), **{x: v for x, v in ek.items() if v is not None}}
    yanit = (yanit or "").strip()[:YANIT_SINIRI]
    sonuc["kayit"] = _kaydet(ajan, brif, yanit, sonuc)
    ofis.ekip_bitti(ajan_id, durum, yanit, sonuc["sure"], sonuc["kayit"])
    return {**sonuc, "yanit": yanit}


# --- komut satırı ------------------------------------------------------------------

def _arg(argv, ad, varsayilan=None):
    return argv[argv.index(ad) + 1] if ad in argv and argv.index(ad) + 1 < len(argv) else varsayilan


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    if argv[0] == "liste":
        veri = ekip()
        c = veri["ceo"]
        print(f"CEO  {c['id']:<17} {c['ad']:<17} {c['model']}")
        for a in veri["ajanlar"]:
            print(f"     {a['id']:<17} {a['ad']:<17} {veri['aileler'][a['aile']]['ad']:<12} "
                  f"{a.get('model') or '(varsayılan)':<26} {a['rol']}")
        return 0
    if argv[0] == "ver" and len(argv) > 1:
        sinyalleri_yakala()
        brif = _arg(argv, "--brif")
        dosya = _arg(argv, "--brif-dosyasi")
        if dosya:
            brif = Path(dosya).read_text(encoding="utf-8")
        sonuc = ver(argv[1], brif, cwd=_arg(argv, "--cwd"), arastirma="--arastirma" in argv,
                    yaz="--yaz" in argv, sure=int(_arg(argv, "--sure", VARSAYILAN_SURE)))
        print(json.dumps(sonuc, ensure_ascii=False))
        return 0 if sonuc["durum"] == "tamam" else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
