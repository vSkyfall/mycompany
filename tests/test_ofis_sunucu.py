"""Ofis sunucusu (bin/ofis_sunucu.py): veri, dosya sınırları ve yazma isteklerinin kapısı."""
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "bin"))
import ayar  # noqa: E402
import ofis_sunucu  # noqa: E402

KOSU = """# Koşu — x-icerik — 2026-11-08T10:00:00+03:00

iş bitti

---
- maliyet: 0.420 USD · tur: 12 · hata: False


## Bekçi
- karar: **kabul**
- gerekçe: temiz
"""


class SunucuTesti(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.kok = tmp / "repo"
        shutil.copytree(KOK / "sirket", self.kok / "sirket")
        (self.kok / "sirket" / "ofis.json").write_text('{"icerik_takimlari": true}', encoding="utf-8")
        shutil.copytree(KOK / "takimlar", self.kok / "takimlar",
                        ignore=shutil.ignore_patterns("kosu", "cikti", "gelen", "veri", "*.jsonl"))
        kosu = self.kok / "takimlar/x-icerik/kosu"
        kosu.mkdir(parents=True)
        (kosu / "2026-11-08-1000.md").write_text(KOSU, encoding="utf-8")
        (kosu / "2026-11-08-0700.md").write_text("# Koşu\n**Atlandı:** mesai dışı\n", encoding="utf-8")
        (kosu / "notlar.txt").write_text("gizli", encoding="utf-8")
        self._ortam = mock.patch.dict(os.environ, {"OFIS_BESLEME": str(tmp / "cubicle.json")})
        self._ortam.start()

    def tearDown(self):
        self._ortam.stop()
        self._tmp.cleanup()

    def test_durum_kosulari_parayi_ve_ozeti_toplar(self):
        simdi = datetime(2026, 11, 8, 11, 0).astimezone()
        d = ofis_sunucu.durum(self.kok, simdi)
        self.assertEqual([k["sonuc"] for k in d["kosular"]], ["tamam", "atlandi"])
        self.assertEqual(d["kosular"][0]["maliyet"], 0.42)
        self.assertEqual(d["kosular"][0]["bekci"], "kabul")
        self.assertEqual(d["para"]["bugun"], 0.42)
        self.assertEqual(d["son3saat"], {"kosu": 1, "tamam": 1, "red": 0, "atlandi": 0, "usd": 0.42})
        self.assertTrue({"x-icerik", "youtube-analiz", "twitter-icerik", "bekci", "fable"}
                        <= {a["id"] for a in d["ajanlar"]})

    def test_kosu_metni_yalniz_kosu_kayitlarini_okur(self):
        self.assertIn("iş bitti", ofis_sunucu.kosu_metni(self.kok, "x-icerik", "2026-11-08-1000.md"))
        for takim, dosya in [("x-icerik", "notlar.txt"), ("x-icerik", "../durum.json"),
                             ("../x-icerik", "2026-11-08-1000.md"), ("yok", "2026-11-08-1000.md")]:
            self.assertIsNone(ofis_sunucu.kosu_metni(self.kok, takim, dosya), (takim, dosya))

    def test_is_ver_kuyruga_patron_maddesi_yazar(self):
        tamam, id_ = ofis_sunucu.is_ver(self.kok, "youtube-analiz", "  bu haftayı\nyeniden çek ",
                                        datetime(2026, 11, 8, 12, 30, 5))
        self.assertTrue(tamam)
        self.assertEqual(id_, "not-20261108123005")
        madde = ayar.durum_oku("youtube-analiz", self.kok)["kuyruk"][-1]
        self.assertEqual(madde, {"id": id_, "durum": "bekliyor", "not": "bu haftayı yeniden çek"})
        self.assertFalse(ofis_sunucu.is_ver(self.kok, "youtube-analiz", "   ")[0])
        self.assertFalse(ofis_sunucu.is_ver(self.kok, "yok", "iş")[0])

    def test_robot_koleksiyonu_ust_klasorden_de_okunur(self):
        tmp = Path(self._tmp.name)
        sayfa, kok = tmp / "repo" / "ofis", tmp / "repo"
        (sayfa / "gorseller").mkdir(parents=True)
        (sayfa / "gorseller" / "bekci.png").write_bytes(b"png")
        with mock.patch.object(ofis_sunucu, "SAYFA", sayfa), mock.patch.object(ofis_sunucu, "KOK", kok):
            self.assertEqual(ofis_sunucu.gorseller(), ["bekci"])
            (tmp / "robot-koleksiyonu.png").write_bytes(b"png")
            self.assertEqual(ofis_sunucu.gorseller(), ["bekci", "robot-koleksiyonu"])
            self.assertEqual(ofis_sunucu.gorsel_yolu("robot-koleksiyonu"), tmp / "robot-koleksiyonu.png")
            self.assertIsNone(ofis_sunucu.gorsel_yolu("bekci-yok"))
            (tmp / "x-icerik.png").write_bytes(b"png")   # üst klasörden yalnız koleksiyon okunur
            self.assertIsNone(ofis_sunucu.gorsel_yolu("x-icerik"))

    def test_kostur_bilinmeyen_takimi_reddeder(self):
        self.assertEqual(ofis_sunucu.kostur(self.kok, "../bin"), (False, "takım yok"))


class HttpTesti(SunucuTesti):
    def setUp(self):
        super().setUp()
        self.sv = ofis_sunucu.sunucu(0, self.kok)
        self.port = self.sv.server_address[1]
        self.sv.RequestHandlerClass.port = self.port
        threading.Thread(target=self.sv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.sv.shutdown()
        self.sv.server_close()
        super().tearDown()

    def istek(self, yol, govde=None, basliklar=None):
        istek = urllib.request.Request(f"http://127.0.0.1:{self.port}{yol}",
                                       data=None if govde is None else json.dumps(govde).encode(),
                                       headers=basliklar or {})
        try:
            with urllib.request.urlopen(istek, timeout=10) as y:
                return y.status, json.loads(y.read() or b"null")
        except urllib.error.HTTPError as h:
            return h.code, json.loads(h.read() or b"null")

    def sayfadan(self):
        return {"Origin": f"http://127.0.0.1:{self.port}", "Content-Type": "application/json"}

    def test_durum_okunur(self):
        kod, veri = self.istek("/api/durum")
        self.assertEqual(kod, 200)
        self.assertEqual(veri["sirket"], "mycompany")

    def test_yabanci_host_reddedilir(self):
        kod, _ = self.istek("/api/durum", basliklar={"Host": "kotu.ornek:80"})
        self.assertEqual(kod, 403)

    def test_yazma_yalniz_bu_sayfadan(self):
        govde = {"takim": "x-icerik", "metin": "dene"}
        self.assertEqual(self.istek("/api/is", govde, {"Content-Type": "application/json"})[0], 403)
        self.assertEqual(self.istek("/api/is", govde, {"Origin": "http://kotu.ornek",
                                                       "Content-Type": "application/json"})[0], 403)
        self.assertEqual(self.istek("/api/is", govde, {"Origin": f"http://127.0.0.1:{self.port}",
                                                       "Content-Type": "text/plain"})[0], 403)
        kod, veri = self.istek("/api/is", govde, self.sayfadan())
        self.assertEqual(kod, 200)
        self.assertTrue(veri["tamam"])

    def test_gordum_ve_kosu_kaydi(self):
        self.assertEqual(self.istek("/api/gordum", {"takim": "x-icerik"}, self.sayfadan())[0], 200)
        self.assertEqual(self.istek("/api/gordum", {"takim": "yok"}, self.sayfadan())[0], 400)
        kod, veri = self.istek("/api/kosu?takim=x-icerik&dosya=2026-11-08-1000.md")
        self.assertEqual(kod, 200)
        self.assertIn("Bekçi", veri["metin"])
        self.assertEqual(self.istek("/api/kosu?takim=x-icerik&dosya=notlar.txt")[0], 404)

    def test_gorsel_adi_disina_cikilamaz(self):
        self.assertEqual(self.istek("/gorsel/..%2F..%2F.env.png")[0], 404)
        self.assertEqual(self.istek("/gorsel/yok-boyle-bir-sey.png")[0], 404)


if __name__ == "__main__":
    unittest.main()
