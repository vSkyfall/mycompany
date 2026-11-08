#!/usr/bin/env python3
"""X Article kapağı üretir — 3840×736 (5,2:1), tek satır başlık.

Hibrit yol: fal (`nano-banana-pro`) **yalnızca zemini** çizer (metinsiz), başlık zeminin üstüne
yerelde PIL ile basılır. Gerekçe: üretken modeller Türkçe metni, tırnakları ve noktalama işaretlerini
bozuyor; kapak başlığı pazarlık konusu değil.

Kullanım:
  python3 bin/kapak_uret.py "<başlık>" <cikti.png> [--zemin "<İngilizce sahne tarifi>"]

Çıkış kodları: 0 üretildi · 2 FAL_KEY yok · 1 üretilemedi.
2 ve 1 durumunda çağıran pakete **"kapak: sen ekleyeceksin"** notunu yazar ve devam eder.
FAL_KEY yalnızca ortamdan okunur; hiçbir çıktıya, kayda, deftere yazılmaz.
"""
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ayar  # noqa: E402

KUYRUK = "https://queue.fal.run"
MODEL = "fal-ai/nano-banana-pro"
DENEMELER = (("21:9", "4K"), ("21:9", "2K"), ("16:9", "2K"))
BEKLEME_SN = 240
GENISLIK, YUKSEKLIK = 3840, 736
METIN_ALANI = 0.52      # sol yarı metne, sağ yarı görsele
KENAR = 170
METIN_RENGI = (27, 23, 19)

ZEMIN_VARSAYILAN = ("a quiet desk still life: brass instruments, folded charts and a single warm "
                    "lamp on dark wood")
ZEMIN_STIL = (" — fine engraved illustration on warm aged paper, muted ink browns with one warm "
              "accent colour, soft vignette, side light from the right, the LEFT HALF of the frame "
              "nearly empty paper for text, absolutely no text, no letters, no numbers, no logo, "
              "no watermark, no signature")
YEDEK_FONTLAR = ("/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
                 "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf")


def _istek(url, veri=None):
    istek = urllib.request.Request(
        url, data=json.dumps(veri).encode() if veri is not None else None,
        headers={"Authorization": f"Key {os.environ.get('FAL_KEY', '')}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(istek, timeout=180) as yanit:
        return json.loads(yanit.read())


def _bekle(is_, sure=BEKLEME_SN):
    """Kuyruk işi bitene kadar yoklar; üretilen görselin URL'ini döner, olmazsa None."""
    biter = time.time() + sure
    while time.time() < biter:
        try:
            durum = _istek(is_["status_url"]).get("status")
        except (urllib.error.URLError, OSError, ValueError, KeyError):
            time.sleep(4)
            continue
        if durum == "COMPLETED":
            sonuc = _istek(is_["response_url"])
            return (sonuc.get("images") or [{}])[0].get("url")
        if durum in ("FAILED", "ERROR"):
            print("kapak: fal üretimi başarısız", file=sys.stderr)
            return None
        time.sleep(4)
    print(f"kapak: {sure} sn içinde bitmedi", file=sys.stderr)
    return None


def zemin_uret(prompt):
    """Kabul edilen ilk oran/çözünürlükle zemini üretir, indirir, geçici dosya yolunu döner."""
    for oran, cozunurluk in DENEMELER:
        try:
            is_ = _istek(f"{KUYRUK}/{MODEL}", {"prompt": prompt, "aspect_ratio": oran,
                                               "resolution": cozunurluk, "num_images": 1})
        except (urllib.error.URLError, OSError, ValueError) as exc:
            print(f"kapak: {oran}/{cozunurluk} kabul edilmedi ({type(exc).__name__}), sıradaki denenecek")
            continue
        url = _bekle(is_)
        if url:
            ham = Path(tempfile.mkstemp(prefix="kapak-ham-", suffix=".png")[1])
            urllib.request.urlretrieve(url, ham)
            return ham
    return None


def font_yolu():
    """Sistemde kurulu bir serif; hiçbiri yoksa None (PIL varsayılanı kullanılır)."""
    for klasor in (Path.home() / "Library/Fonts", Path("/Library/Fonts")):
        bulunan = sorted(klasor.glob("*[Ff]raunces*.ttf")) if klasor.is_dir() else []
        if bulunan:
            return str(bulunan[0])
    return next((y for y in YEDEK_FONTLAR if Path(y).exists()), None)


def _sigan_font(cizim, yol, metin, en_fazla_genislik):
    """Tek satıra sığana kadar puntoyu küçültür (en az 72)."""
    from PIL import ImageFont
    for boyut in range(190, 71, -6):
        font = ImageFont.truetype(yol, boyut) if yol else ImageFont.load_default()
        if not yol or cizim.textlength(metin, font=font) <= en_fazla_genislik:
            return font
    return ImageFont.truetype(yol, 72)


def kirp_ve_yaz(ham, baslik, cikti):
    """Zemini 3840×736'ya kırpar, başlığı sola basar, PNG yazar."""
    from PIL import Image, ImageDraw
    with Image.open(ham) as gorsel:
        kaynak = gorsel.convert("RGB")
        olcek = max(GENISLIK / kaynak.width, YUKSEKLIK / kaynak.height)
        buyuk = kaynak.resize((round(kaynak.width * olcek), round(kaynak.height * olcek)), Image.LANCZOS)
    sol, ust = (buyuk.width - GENISLIK) // 2, (buyuk.height - YUKSEKLIK) // 2
    kapak = buyuk.crop((sol, ust, sol + GENISLIK, ust + YUKSEKLIK))
    cizim = ImageDraw.Draw(kapak)
    font = _sigan_font(cizim, font_yolu(), baslik, METIN_ALANI * GENISLIK - 2 * KENAR)
    kutu = cizim.textbbox((0, 0), baslik, font=font)
    cizim.text((KENAR, (YUKSEKLIK - (kutu[3] - kutu[1])) // 2 - kutu[1]), baslik, font=font, fill=METIN_RENGI)
    Path(cikti).parent.mkdir(parents=True, exist_ok=True)
    kapak.save(cikti, "PNG")
    return cikti


def uret(baslik, cikti, zemin=None):
    ham = zemin_uret((zemin or ZEMIN_VARSAYILAN) + ZEMIN_STIL)
    if not ham:
        return None
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("kapak: PIL yok (pip install pillow) — başlık basılamadı", file=sys.stderr)
        return None
    return kirp_ve_yaz(ham, baslik, cikti)


def main(argv):
    ayar.ortam_yukle()
    if len(argv) < 2:
        print(__doc__)
        return 1
    if not os.environ.get("FAL_KEY"):
        print("kapak üretilmedi: FAL_KEY yok — pakete 'kapak: sen ekleyeceksin' notu düş", file=sys.stderr)
        return 2
    zemin = argv[argv.index("--zemin") + 1] if "--zemin" in argv[:-1] else None
    yol = uret(argv[0], argv[1], zemin)
    if not yol:
        print("kapak üretilemedi — pakete 'kapak: sen ekleyeceksin' notu düş", file=sys.stderr)
        return 1
    print(f"kapak: {yol} ({GENISLIK}×{YUKSEKLIK})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
