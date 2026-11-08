"""Ofis beslemesi (bin/ofis.py): Cubicle'ın okuduğu JSON'un durum dosyalarından doğru kurulması."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "bin"))
import ayar  # noqa: E402
import kos  # noqa: E402
import ofis  # noqa: E402


class OfisTesti(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.kok = tmp / "repo"
        shutil.copytree(KOK / "sirket", self.kok / "sirket")
        (self.kok / "sirket" / "ofis.json").write_text('{"icerik_takimlari": true}', encoding="utf-8")
        shutil.copytree(KOK / "takimlar", self.kok / "takimlar",
                        ignore=shutil.ignore_patterns("kosu", "cikti", "gelen", "veri", "*.jsonl"))
        for durum in (self.kok / "takimlar").glob("*/durum.json"):   # gerçek koşulardan bağımsız, temiz durum
            durum.write_text((KOK / "takimlar" / "_iskelet" / "durum.json").read_text(encoding="utf-8")
                             .replace('"TAKIM"', f'"{durum.parent.name}"'), encoding="utf-8")
        self.besleme = tmp / "cubicle" / "a-sirketi.json"
        self._ortam = mock.patch.dict(os.environ, {"OFIS_BESLEME": str(self.besleme)})
        self._ortam.start()
        os.environ.pop("OFIS_KAPALI", None)

    def tearDown(self):
        self._ortam.stop()
        self._tmp.cleanup()

    def ajanlar(self):
        return {a["id"]: a for a in json.loads(self.besleme.read_text(encoding="utf-8"))["agents"]}

    def durum(self, takim, **yama):
        ayar.durum_guncelle(takim, yama, self.kok)

    def test_her_takim_bir_calisan_artı_bekci(self):
        self.assertTrue(ofis.yaz(self.kok))
        veri = json.loads(self.besleme.read_text(encoding="utf-8"))
        self.assertEqual(veri["company"], "mycompany")
        self.assertEqual(veri["view"], "http://127.0.0.1:3210/")
        self.assertEqual([a["id"] for a in veri["agents"]][:5],
                         ["twitter-icerik", "x-icerik", "youtube-analiz", "bekci", "fable"])
        self.assertEqual(len(veri["agents"]), 4 + 13)   # takımlar + bekçi, CEO + 12 ajan
        self.assertTrue(all(a["status"] == "idle" for a in veri["agents"]))

    def test_durum_yazimi_ofisi_tazeler(self):
        self.durum("x-icerik", kuyruk=[{"id": "x-77", "durum": "bekliyor", "not": "link"}])
        self.assertEqual(self.ajanlar()["x-icerik"]["task"], "kuyrukta 1 iş · sıradaki x-77")

    def test_son_halka_tamam_el_kaldirir_zincir_halkasi_molaya_gider(self):
        self.durum("twitter-icerik", son_sonuc="tamam", son_kosu="2026-11-08T10:00:00+03:00")
        self.durum("x-icerik", son_sonuc="tamam", son_kosu="2026-11-08T09:00:00+03:00")
        ajanlar = self.ajanlar()
        self.assertEqual(ajanlar["twitter-icerik"]["status"], "waiting")
        self.assertIn("yayın düğmesi sende", ajanlar["twitter-icerik"]["task"]["title"])
        self.assertEqual(ajanlar["x-icerik"]["status"], "idle")
        self.assertEqual(ajanlar["x-icerik"]["completedAt"], "2026-11-08T09:00:00+03:00")

    def test_gordum_eli_indirir_yeni_kosu_yeniden_kaldirir(self):
        self.durum("twitter-icerik", son_sonuc="tamam", son_kosu="2026-11-08T10:00:00+03:00")
        ofis.gordum("twitter-icerik", self.kok)
        self.assertEqual(self.ajanlar()["twitter-icerik"]["status"], "idle")
        ofis.basladi("twitter-icerik", self.kok)
        ofis.bitti("twitter-icerik", self.kok)
        self.durum("twitter-icerik", son_sonuc="tamam", son_kosu="2026-11-08T11:00:00+03:00")
        self.assertEqual(self.ajanlar()["twitter-icerik"]["status"], "waiting")

    def test_red_hata_ve_atlanma(self):
        self.durum("x-icerik", son_sonuc="red", bekci={"son_karar": "red", "gerekce": "kaynak yok"})
        self.durum("youtube-analiz", son_sonuc="hata")
        kosu = self.kok / "takimlar/twitter-icerik/kosu/2026-11-08-0100.md"
        kosu.parent.mkdir(parents=True)
        kosu.write_text("# koşu\n**Atlandı:** mesai dışı (09:00-23:00); kuyrukta bekler\n", encoding="utf-8")
        self.durum("twitter-icerik", son_sonuc="atlandi")
        ajanlar = self.ajanlar()
        self.assertEqual(ajanlar["x-icerik"]["status"], "error")
        self.assertEqual(ajanlar["x-icerik"]["error"], "bekçi red: kaynak yok")
        self.assertEqual(ajanlar["youtube-analiz"]["status"], "error")
        self.assertEqual(ajanlar["twitter-icerik"]["status"], "paused")
        self.assertTrue(ajanlar["twitter-icerik"]["task"].startswith("mesai dışı"))

    def test_kosu_masada_adimlar_kartta(self):
        self.durum("x-icerik", kuyruk=[{"id": "x-9", "durum": "bekliyor", "not": "tweet doğrula"}])
        ofis.basladi("x-icerik", self.kok)
        ajan = self.ajanlar()["x-icerik"]
        self.assertEqual(ajan["status"], "running")
        self.assertEqual(ajan["task"], {"id": "x-9", "title": "tweet doğrula"})
        olay = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                "tool_input": {"command": "python3 bin/tweet_cek.py https://x.com/a/status/1"}}
        ofis.kanca_isle(olay, "x-icerik", self.kok)
        self.assertEqual(len(self.ajanlar()["x-icerik"]["recent"][0]), 2)   # sürüyor
        ofis.kanca_isle({**olay, "hook_event_name": "PostToolUse"}, "x-icerik", self.kok)
        adim = self.ajanlar()["x-icerik"]["recent"][0]
        self.assertEqual(adim[1], "Bash: python3 bin/tweet_cek.py https://x.com/a/status/1")
        self.assertEqual(len(adim), 3)
        ofis.bitti("x-icerik", self.kok)
        self.assertNotEqual(self.ajanlar()["x-icerik"]["status"], "running")

    def test_cokmus_kosu_sonsuza_dek_masada_kalmaz(self):
        ofis.basladi("x-icerik", self.kok)
        canli = json.loads(ofis._canli_yolu().read_text(encoding="utf-8"))
        canli["kosan"]["x-icerik"]["basla"] -= (ofis.TAZE_SN + 1) * 1000
        ofis._canli_yolu().write_text(json.dumps(canli), encoding="utf-8")
        ofis.yaz(self.kok)
        self.assertEqual(self.ajanlar()["x-icerik"]["status"], "idle")

    def test_bekci_denetlerken_masada_sonra_son_karari_soyler(self):
        ofis.bekci_basladi("x-icerik", self.kok)
        bekci = self.ajanlar()["bekci"]
        self.assertEqual(bekci["status"], "running")
        self.assertEqual(bekci["parent"], "x-icerik")
        self.durum("x-icerik", bekci={"son_karar": "kabul", "zaman": "2026-11-08T10:00:00+03:00"})
        ofis.bekci_bitti(self.kok)
        bekci = self.ajanlar()["bekci"]
        self.assertEqual(bekci["status"], "idle")
        self.assertEqual(bekci["task"], "son karar: kabul — x-icerik")

    def test_ofis_kapali_hicbir_sey_yazmaz(self):
        with mock.patch.dict(os.environ, {"OFIS_KAPALI": "1"}):
            self.assertFalse(ofis.yaz(self.kok))
            ofis.basladi("x-icerik", self.kok)
        self.assertFalse(self.besleme.exists())

    def test_yabanci_kok_besleme_yolu_verilmezse_yazilmaz(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OFIS_BESLEME")
            self.assertFalse(ofis._acik(self.kok))
            self.assertTrue(ofis._acik(ofis.GERCEK_KOK))

    def test_kanca_komut_satirindan_calisir_ve_stdouta_yazmaz(self):
        olay = {"hook_event_name": "PreToolUse", "tool_name": "WebSearch", "tool_input": {"query": "kaynak"}}
        sonuc = subprocess.run([sys.executable, str(KOK / "bin/ofis.py"), "--hook"],
                               input=json.dumps(olay), capture_output=True, text=True, timeout=30,
                               env={**os.environ, "SIRKET_TAKIM": "x-icerik"})
        self.assertEqual(sonuc.returncode, 0)
        self.assertEqual(sonuc.stdout, "")
        canli = json.loads(ofis._canli_yolu().read_text(encoding="utf-8"))
        self.assertEqual(canli["adimlar"]["x-icerik"][0][1], "WebSearch: kaynak")

    def test_kanca_sirket_kosusu_disinda_karismaz(self):
        olay = {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {"file_path": "/a/b.md"}}
        env = {k: v for k, v in os.environ.items() if k != "SIRKET_TAKIM"}
        sonuc = subprocess.run([sys.executable, str(KOK / "bin/ofis.py"), "--hook"],
                               input=json.dumps(olay), capture_output=True, text=True, timeout=30, env=env)
        self.assertEqual(sonuc.returncode, 0)
        self.assertFalse(ofis._canli_yolu().exists())


class KomutTesti(unittest.TestCase):
    def test_sirket_kosusu_kullanici_ayarlarindan_yalitilir_ofis_kancasini_tasir(self):
        komut = kos.claude_komutu("merhaba", ["Read"], 2)
        self.assertEqual(komut[komut.index("--setting-sources") + 1], "project,local")
        ayarlar = json.loads(komut[komut.index("--settings") + 1])
        for olay in ("PreToolUse", "PostToolUse"):
            kanca = ayarlar["hooks"][olay][0]["hooks"][0]
            self.assertIn(str(KOK / "bin" / "ofis.py"), kanca["command"])
            self.assertTrue(kanca["command"].endswith("--hook"))

    def test_adim_ozeti(self):
        self.assertEqual(ofis.adim_ozeti("Read", {"file_path": "/x/takimlar/a/kurallar.md"}), "Read: kurallar.md")
        self.assertEqual(ofis.adim_ozeti("WebFetch", {"url": "https://ornek.com/a/b"}), "WebFetch: ornek.com")
        self.assertTrue(ofis.adim_ozeti("Bash", {"command": "x" * 200}).endswith("…"))
        self.assertEqual(ofis.adim_ozeti("TodoWrite", {}), "TodoWrite")


if __name__ == "__main__":
    unittest.main()
