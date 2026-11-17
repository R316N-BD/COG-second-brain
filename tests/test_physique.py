import datetime as dt
import tempfile
import unittest
from pathlib import Path

from cog_core.physique import Vault, summary, validate_record

def row(date, weight=80):
    return dict(date=date, weight_kg=weight, sleep_hours=None,
                training_minutes=45, adherence_pct=90)

class PhysiqueTest(unittest.TestCase):
    def test_validation(self):
        for invalid in (float("nan"), True, -1, 501):
            with self.assertRaises(ValueError):
                validate_record(row("2026-01-01", invalid))
        with self.assertRaises(ValueError):
            validate_record(row("2026-02-30"))

    def test_summary(self):
        state={"version":1,"target_date":"2026-01-21",
               "records":[row("2026-01-01",80),row("2026-01-12",78),row("2026-01-14",76)]}
        result=summary(state,dt.date(2026,1,14))
        self.assertEqual(result["days_until_target"],7)
        self.assertEqual(result["metrics"]["weight_kg"]["change"],-3)
        self.assertEqual(result["metrics"]["sleep_hours"]["last_7_days"]["count"],0)

    def test_encryption_and_mutations(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/"config").mkdir()
            (root/"config/cog.json").write_text("{}")
            vault=Vault(root)
            password="synthetic-test-passphrase"
            vault.initialize(password)
            vault.add(password,row("2026-01-14"))
            with self.assertRaises(ValueError):
                vault.add(password,row("2026-01-14"))
            self.assertNotIn(b"weight_kg",vault.path.read_bytes())
            with self.assertRaises(ValueError):
                vault.read("incorrect-test-passphrase")
            vault.replace(password,row("2026-01-14",81))
            self.assertEqual(vault.read(password)["records"][0]["weight_kg"],81)
            vault.delete(password,"2026-01-14")
            self.assertEqual(vault.read(password)["records"],[])
            blob=vault.path.read_bytes()
            vault.path.write_bytes(blob[:-1]+bytes([blob[-1]^1]))
            with self.assertRaises(ValueError):
                vault.read(password)
