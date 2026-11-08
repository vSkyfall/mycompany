"""`bin/agents_uret.py` — takim.md → .claude/agents/<t>.md ve kimlik önsözü.

Ana şirketin `tests/test_agents_uret.py` dosyasından üç takıma uyarlandı.
"""
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "bin"))
import agents_uret as au  # noqa: E402

ORNEK = """---
name: deneme
description: Deneme takımı — test.
model: sonnet
tools: [Read, Write, Glob]
gerekli_anahtarlar: [TELEGRAM_BOT_TOKEN]
skills: [kaynak-dogrulama, zincir-yazimi]
butce_usd: 2
---

# Deneme

Gövde metni.
"""


class AgentsUretTesti(unittest.TestCase):
    def test_frontmatter_ayristirma(self):
        fm, govde = au.ayristir(ORNEK)
        self.assertEqual(fm["name"], "deneme")
        self.assertEqual(fm["tools"], ["Read", "Write", "Glob"])
        self.assertEqual(fm["gerekli_anahtarlar"], ["TELEGRAM_BOT_TOKEN"])
        self.assertIn("Gövde metni.", govde)

    def test_agent_dosyasi_sirket_alanlarini_atar_ve_onsoz_ekler(self):
        cikti = au.agent_metni("deneme", ORNEK)
        self.assertIn("name: deneme", cikti)
        self.assertIn("tools: Read, Write, Glob", cikti)
        self.assertNotIn("gerekli_anahtarlar", cikti)
        self.assertNotIn("butce_usd", cikti)
        self.assertIn("Gövde metni.", cikti)

    def test_ilk_satir_kimlik(self):
        """Ajan dosyasının gövdesinin İLK SATIRI: kim olduğun + mesleğin."""
        cikti = au.agent_metni("deneme", ORNEK)
        ilk = cikti.split("---\n", 2)[2].lstrip().splitlines()[0]
        self.assertTrue(ilk.startswith("> **Sen `deneme` ajanısın.**"), ilk)
        self.assertIn("A Şirketi'nde bir çalışansın", ilk)
        self.assertIn("bir yapay zekâ ajanısın", ilk)
        self.assertIn("Mesleğin: Deneme takımı — test.", ilk)

    def test_okuma_sirasi_anayasa_kimlik_kurallar(self):
        cikti = au.agent_metni("deneme", ORNEK)
        self.assertIn("sirket/AJAN-KIMLIGI.md", cikti)
        self.assertLess(cikti.index("ANAYASA.md"), cikti.index("sirket/AJAN-KIMLIGI.md"))
        self.assertLess(cikti.index("sirket/AJAN-KIMLIGI.md"), cikti.index("takimlar/deneme/kurallar.md"))

    def test_skills_sirket_alanidir_agent_frontmatterina_sizmaz(self):
        fm, _ = au.ayristir(ORNEK)
        self.assertEqual(fm["skills"], ["kaynak-dogrulama", "zincir-yazimi"])
        self.assertIn("skills", au.SIRKET_ALANLARI)
        ust = au.agent_metni("deneme", ORNEK).split("---", 2)[1]
        self.assertNotIn("skills:", ust)

    def test_onsoz_yetenek_satiri_ekler(self):
        cikti = au.agent_metni("deneme", ORNEK)
        self.assertIn("Yeteneklerin: `skills/kaynak-dogrulama/SKILL.md`, `skills/zincir-yazimi/SKILL.md`", cikti)
        self.assertIn("ilgili adımda oku ve uygula", cikti)

    def test_skills_yoksa_yetenek_satiri_yok(self):
        ham = ORNEK.replace("skills: [kaynak-dogrulama, zincir-yazimi]\n", "")
        self.assertNotIn("Yeteneklerin:", au.agent_metni("deneme", ham))

    def test_onsoz_kendini_gelistirme_cumlesi(self):
        cikti = au.agent_metni("deneme", ORNEK)
        self.assertIn("kendini geliştir", cikti)
        self.assertIn("defter.md", cikti)

    def test_meslek_bos_birakilmaz(self):
        ham = ORNEK.replace("description: Deneme takımı — test.\n", "")
        self.assertIn("Mesleğin: bu takımın işini yapmak.", au.agent_metni("deneme", ham))

    def test_uret_ve_check(self):
        with tempfile.TemporaryDirectory() as d:
            kok = Path(d)
            (kok / "takimlar/deneme").mkdir(parents=True)
            (kok / "takimlar/deneme/takim.md").write_text(ORNEK, encoding="utf-8")
            self.assertEqual(au.uret(kok), ["deneme"])
            self.assertTrue((kok / ".claude/agents/deneme.md").exists())
            self.assertEqual(au.uret(kok, sadece_kontrol=True), [])
            (kok / ".claude/agents/deneme.md").write_text("bozuk", encoding="utf-8")
            self.assertEqual(au.uret(kok, sadece_kontrol=True), ["deneme"])

    def test_iskelet_takimi_uretilmez(self):
        with tempfile.TemporaryDirectory() as d:
            kok = Path(d)
            (kok / "takimlar/_iskelet").mkdir(parents=True)
            (kok / "takimlar/_iskelet/takim.md").write_text(ORNEK, encoding="utf-8")
            self.assertEqual(au.uret(kok), [])

    def test_repodaki_uc_takim_uretilebiliyor(self):
        for takim in ("x-icerik", "youtube-analiz", "twitter-icerik"):
            with self.subTest(takim=takim):
                ham = (KOK / "takimlar" / takim / "takim.md").read_text(encoding="utf-8")
                cikti = au.agent_metni(takim, ham)
                ilk = cikti.split("---\n", 2)[2].lstrip().splitlines()[0]
                self.assertTrue(ilk.startswith(f"> **Sen `{takim}` ajanısın.**"), ilk)
                self.assertIn("Yeteneklerin:", cikti)


if __name__ == "__main__":
    unittest.main()
