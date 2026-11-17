import datetime as dt
import tempfile
import unittest
from pathlib import Path
from cog_core import physique as p
from cog_core import physique_training as t

class PhysiqueV2Tests(unittest.TestCase):
    def test_migration(self):
        old={"version":1,"target_date":"2027-02-01","records":[{"date":"2026-11-16","weight_kg":90,"sleep_hours":7,"training_minutes":60,"adherence_pct":95}]}
        new=p.validate_state(old)
        self.assertEqual(new["version"],2)
        self.assertEqual(new["records"],old["records"])
        self.assertEqual(new["sets"],[])
        self.assertEqual(old["version"],1)
    def test_analytics(self):
        rows=[t.new_set("2026-11-17","Squat",8,100),t.new_set("2026-11-16","squat",5,120),t.new_set("2026-11-09","Squat",10,80),t.new_set("2026-11-18","Squat",10,200)]
        milestone=t.new_milestone("2026-11-16","Register for show")
        report=t.analytics({"sets":rows,"milestones":[milestone]},dt.date(2026,11,17))
        self.assertEqual(report["current"]["volume_kg"],1400)
        self.assertEqual(report["prior"]["volume_kg"],800)
        self.assertEqual(report["current"]["sessions"],2)
        self.assertEqual(report["best_sets"][0]["weight_kg"],120)
        self.assertEqual(report["overdue"],1)
    def test_invalid(self):
        for reps in (True,0,501,1.5):
            with self.assertRaises(ValueError):t.new_set("2026-11-17","Bench",reps,80)
        with self.assertRaises(ValueError):t.new_set("2026-11-17","Bench",8,float("nan"))
        with self.assertRaises(ValueError):t.new_milestone("2026-02-30","Show")
        row=t.new_set("2026-11-17","Bench",8,80)
        with self.assertRaises(ValueError):t.validate_collections({"sets":[row,row],"milestones":[]})
    def test_vault_roundtrip(self):
        try: p._crypto()
        except ValueError: self.skipTest("cryptography unavailable")
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); (root/"config").mkdir();(root/"config/cog.json").write_text("{}")
            vault=p.Vault(root);password="test-only-strong-passphrase"
            vault.initialize(password)
            row=t.new_set("2026-11-17","Bench",8,80,8)
            milestone=t.new_milestone("2026-12-01","Registration")
            vault.add_set(password,row);vault.add_milestone(password,milestone)
            self.assertEqual(vault.read(password)["sets"],[row])
            vault.change_item(password,"milestones",milestone["id"],"toggle")
            self.assertTrue(vault.read(password)["milestones"][0]["done"])
            self.assertNotIn(b"Bench",vault.path.read_bytes())
            with self.assertRaises(ValueError):vault.read("incorrect-long-passphrase")
            vault.change_item(password,"sets",row["id"],"delete")
            self.assertEqual(vault.read(password)["sets"],[])
if __name__=="__main__":unittest.main()
