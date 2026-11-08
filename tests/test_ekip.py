"""Ekip dağıtıcısı (bin/ekip.py), CEO koşusu (bin/ceo.py) ve ofisteki karşılıkları."""
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
import ceo  # noqa: E402
import ekip  # noqa: E402
import ofis  # noqa: E402
import ofis_sunucu  # noqa: E402


def ajan(ajan_id):
    return ekip.ajan_bul(ajan_id)


class KayitTesti(unittest.TestCase):
    def test_ekip_on_iki_ajan_ve_ceo(self):
        veri = ekip.ekip()
        self.assertEqual(veri["ceo"]["model"], "claude-fable-5-1")
        self.assertEqual(len(veri["ajanlar"]), 12)
        aileler = [a["aile"] for a in veri["ajanlar"]]
        self.assertEqual((aileler.count("claude"), aileler.count("antigravity"), aileler.count("codex")), (3, 5, 4))
        self.assertEqual(len({a["id"] for a in veri["ajanlar"]}), 12)
        for a in veri["ajanlar"]:
            self.assertIn(a["aile"], veri["aileler"])


class KomutTesti(unittest.TestCase):
    def test_claude_salt_okunur_ve_kullanici_ayarindan_yalitik(self):
        k = ekip.komut(ajan("claude-sonnet"), "işi yap", Path("/tmp"))
        self.assertEqual(k[:3], ["claude", "-p", "işi yap"])
        self.assertEqual(k[k.index("--model") + 1], "claude-sonnet-5-5")
        self.assertNotIn("Write", k[k.index("--allowedTools") + 1])
        self.assertNotIn("Bash", k[k.index("--allowedTools") + 1])
        self.assertNotIn("--max-budget-usd", k)
        self.assertEqual(k[k.index("--setting-sources") + 1], "project,local")
        self.assertNotIn("--permission-mode", k)
        yazan = ekip.komut(ajan("claude-sonnet"), "x", Path("/tmp"), yaz=True)
        self.assertIn("Write", yazan[yazan.index("--allowedTools") + 1])

    def test_antigravity_delege_betigi(self):
        k = ekip.komut(ajan("agy-gemini-argon"), "araştır", Path("/tmp/p"), arastirma=True)
        self.assertTrue(k[0].endswith("delegate.sh"))
        self.assertEqual(k[k.index("--model") + 1], "gemini-4-argon-high")
        self.assertIn("--research", k)
        self.assertNotIn("--write", k)
        self.assertEqual(k[-1], "araştır")
        okur = ekip.komut(ajan("agy-sonnet"), "incele", Path("/tmp/p"))
        self.assertIn("Kabuk komutu çalıştırma", okur[-1])     # salt-okunur agy kabuğa kalkmasın

    def test_codex_salt_okunur_varsayilan_model(self):
        k = ekip.komut(ajan("codex-6-luna"), "incele", Path("/tmp/p"), son_dosya="/tmp/s.txt")
        self.assertEqual(k[:2], ["codex", "exec"])
        self.assertEqual(k[k.index("-s") + 1], "read-only")
        self.assertEqual(k[k.index("-m") + 1], "gpt-6-luna")
        chatgpt = ekip.komut(ajan("chatgpt"), "soru", Path("/tmp/p"), son_dosya="/tmp/s.txt")
        self.assertNotIn("-m", chatgpt)      # hesaptaki varsayılan model


class VerTesti(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._ortam = mock.patch.dict(os.environ, {"OFIS_BESLEME": str(Path(self._tmp.name) / "c.json")})
        self._ortam.start()
        os.environ.pop("MYCOMPANY_YAZMA", None)
        self._log = mock.patch.object(ekip, "KOK", Path(self._tmp.name))
        self._log.start()

    def tearDown(self):
        self._log.stop()
        self._ortam.stop()
        self._tmp.cleanup()

    def sahte(self, stdout="", returncode=0, son_yaz=None):
        cagrilar = []

        def calistir(k, **kw):
            cagrilar.append((k, kw))
            if son_yaz is not None:
                Path(k[k.index("-o") + 1]).write_text(son_yaz, encoding="utf-8")
            return subprocess.CompletedProcess(k, returncode, stdout=stdout, stderr="")
        return calistir, cagrilar

    def test_claude_yaniti_ve_ofis_izi(self):
        calistir, cagrilar = self.sahte(json.dumps({"result": "plan hazır", "total_cost_usd": 0.12}))
        sonuc = ekip.ver("claude-opus", "plan yap", cwd=str(KOK), calistir=calistir)
        self.assertEqual(sonuc["durum"], "tamam")
        self.assertEqual(sonuc["yanit"], "plan hazır")
        self.assertEqual(sonuc["maliyet"], 0.12)
        self.assertNotIn("CLAUDECODE", cagrilar[0][1]["env"])
        kayit = Path(self._tmp.name) / sonuc["kayit"]
        self.assertIn("plan yap", kayit.read_text(encoding="utf-8"))
        son = ofis._canli()["ekip_son"]["claude-opus"]
        self.assertEqual((son["durum"], son["is"]), ("tamam", "plan yap"))
        self.assertNotIn("claude-opus", ofis._canli()["ekip"])

    def test_codex_son_mesaj_dosyasindan_okunur(self):
        calistir, _ = self.sahte(son_yaz="incelendi: 2 sorun")
        sonuc = ekip.ver("codex-terra-56", "incele", cwd=str(KOK), calistir=calistir)
        self.assertEqual((sonuc["durum"], sonuc["yanit"]), ("tamam", "incelendi: 2 sorun"))

    def test_antigravity_takilma_hata_sayilir(self):
        cikti = json.dumps({"exit": 75, "stalled": True, "response": "plan sundum"})
        calistir, _ = self.sahte(cikti)
        self.assertEqual(ekip.ver("agy-sonnet", "yap", cwd=str(KOK), calistir=calistir)["durum"], "hata")

    def test_yazma_izni_yoksa_calismaz(self):
        calistir, cagrilar = self.sahte()
        sonuc = ekip.ver("claude-sonnet", "düzelt", cwd=str(KOK), yaz=True, calistir=calistir)
        self.assertEqual(sonuc["durum"], "hata")
        self.assertIn("yazma izni yok", sonuc["yanit"])
        self.assertEqual(cagrilar, [])

    def test_gecersiz_ajan_bos_brif_ve_klasor(self):
        calistir, cagrilar = self.sahte()
        self.assertIn("ekipte yok", ekip.ver("yok", "x", calistir=calistir)["yanit"])
        self.assertEqual(ekip.ver("claude-haiku", "  ", calistir=calistir)["yanit"], "brif boş")
        self.assertIn("geçersiz", ekip.ver("claude-haiku", "x", cwd="/etc", calistir=calistir)["yanit"])
        self.assertEqual(cagrilar, [])

    def test_zaman_asimi(self):
        def calistir(k, **kw):
            raise subprocess.TimeoutExpired(k, 1)
        sonuc = ekip.ver("claude-haiku", "x", cwd=str(KOK), sure=5, calistir=calistir)
        self.assertEqual(sonuc["durum"], "zaman_asimi")


class OfisTesti(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._ortam = mock.patch.dict(os.environ, {"OFIS_BESLEME": str(Path(self._tmp.name) / "c.json")})
        self._ortam.start()

    def tearDown(self):
        self._ortam.stop()
        self._tmp.cleanup()

    def ajanlar(self):
        return {a["id"]: a for a in ofis.besleme()["agents"]}

    def test_ceo_ve_ekip_ofiste(self):
        a = self.ajanlar()
        self.assertEqual(a["fable"]["status"], "idle")
        self.assertEqual(a["agy-gemini-argon"]["name"], "Gemini 4 Argon · Antigravity")
        self.assertEqual(a["codex-6-luna"]["parent"], "fable")
        self.assertEqual((a["fable"]["desk"], a["fable"]["stay"]), ("front", True))
        self.assertTrue(a["claude-opus"]["stay"])
        ofis.ekip_basladi("codex-6-luna", "kodu incele")
        self.assertEqual(self.ajanlar()["codex-6-luna"]["status"], "running")
        ofis.ekip_bitti("codex-6-luna", "hata", "kota doldu", 3, "k.md")
        self.assertEqual(self.ajanlar()["codex-6-luna"]["status"], "error")

    def test_ceo_raporu_patronu_bekler(self):
        ofis.ceo_basladi("rakip analizi", "2026-11-08-140000")
        self.assertEqual(self.ajanlar()["fable"]["status"], "running")
        ofis.ceo_bitti("tamam", "sirket-log/ceo/2026-11-08-140000/rapor.md", 0.8)
        fable = self.ajanlar()["fable"]
        self.assertEqual(fable["status"], "waiting")
        self.assertIn("rapor hazır", fable["task"])
        ofis.ceo_gordum()
        self.assertEqual(self.ajanlar()["fable"]["status"], "idle")


class CeoTesti(unittest.TestCase):
    def test_istem_ekibi_rolleri_ve_rapor_yolunu_tasir(self):
        metin = ceo.istem("rakip analizi yap", Path("/x/rapor.md"), Path("/proje"), yazabilir=False)
        for a in ekip.ekip()["ajanlar"]:
            self.assertIn(f"`{a['id']}`", metin)
        self.assertIn("/x/rapor.md", metin)
        self.assertIn('--cwd "/proje"', metin)
        self.assertIn("`--yaz` kullanma", metin)
        self.assertIn("`--yaz` ekleyebilirsin", ceo.istem("x", Path("/r"), Path("/p"), yazabilir=True))

    def test_ceo_yalniz_ekip_komutunu_calistirabilir(self):
        k = ceo.komut("istem", ceo.CEO_BUTCESI_USD)
        self.assertEqual(k[k.index("--model") + 1], "claude-fable-5-1")
        araclar = k[k.index("--allowedTools") + 1].split(",")
        self.assertIn("Bash(python3 bin/ekip.py *)", araclar)
        self.assertFalse([a for a in araclar if a.startswith("Bash") and a != "Bash(python3 bin/ekip.py *)"])
        self.assertNotIn("--max-budget-usd", k)                    # para tavanı yok
        self.assertEqual(ceo.komut("istem", 3)[ceo.komut("istem", 3).index("--max-budget-usd") + 1], "3")

    def test_kuru_kosu_hicbir_sey_baslatmaz(self):
        with mock.patch.object(ceo.subprocess, "run") as run:
            self.assertEqual(ceo.kos("deneme", cwd=str(KOK), kuru=True), 0)
        run.assert_not_called()


class SunucuTesti(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.kok = Path(self._tmp.name) / "repo"
        shutil.copytree(KOK / "sirket", self.kok / "sirket")
        k = self.kok / "sirket-log" / "ceo" / "2026-11-08-140000"
        k.mkdir(parents=True)
        (k / "is.md").write_text("# İş\n\nrakip analizi\n", encoding="utf-8")
        (k / "rapor.md").write_text("# Rapor\nsonuç", encoding="utf-8")
        (k / "sonuc.json").write_text('{"durum": "tamam", "maliyet": 0.5}', encoding="utf-8")
        e = self.kok / "sirket-log" / "ekip" / "2026-11-08"
        e.mkdir(parents=True)
        (e / "140501-claude-opus.md").write_text("# Opus\nyanıt", encoding="utf-8")
        self._ortam = mock.patch.dict(os.environ, {"OFIS_BESLEME": str(Path(self._tmp.name) / "c.json")})
        self._ortam.start()

    def tearDown(self):
        self._ortam.stop()
        self._tmp.cleanup()

    def test_rapor_listesi_ve_okuma(self):
        liste = ofis_sunucu.ceo_raporlari(self.kok)
        self.assertEqual(liste[0]["klasor"], "2026-11-08-140000")
        self.assertEqual((liste[0]["durum"], liste[0]["is"].strip()), ("tamam", "rakip analizi"))
        self.assertIn("sonuç", ofis_sunucu.ceo_raporu(self.kok, "2026-11-08-140000"))
        for kotu in ("../sirket", "2026-11-08-140000/../../x", ""):
            self.assertIsNone(ofis_sunucu.ceo_raporu(self.kok, kotu))

    def test_ekip_kaydi_yolu_dogrulanir(self):
        self.assertIn("yanıt", ofis_sunucu.ekip_kaydi_metni(self.kok, "sirket-log/ekip/2026-11-08/140501-claude-opus.md"))
        for kotu in ("sirket/ekip.json", "sirket-log/ekip/2026-11-08/../../.env", "/etc/passwd"):
            self.assertIsNone(ofis_sunucu.ekip_kaydi_metni(self.kok, kotu))

    def test_bos_is_ceoya_gitmez(self):
        with mock.patch.object(ofis_sunucu.subprocess, "Popen") as p:
            self.assertEqual(ofis_sunucu.ceo_ver(self.kok, "   "), (False, "iş metni boş"))
        p.assert_not_called()


if __name__ == "__main__":
    unittest.main()
