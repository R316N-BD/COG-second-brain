import datetime as dt
import math
import unittest
from cog_core.physique_body_detail import REGIONS,DETAIL,region_history,period_comparison,detailed_relationship
from cog_core.physique_body_mesh import PARTS,faces,scene,rotate
from cog_core.physique_training import new_set

class BodyDetailTests(unittest.TestCase):
    def test_catalog_coverage(self):
        self.assertEqual(len(REGIONS),30)
        self.assertEqual({p[0] for p in PARTS if p[0]},set(REGIONS))
        for primary,secondary in DETAIL.values():
            self.assertFalse(set(primary)&set(secondary))
            self.assertTrue(set(primary+secondary)<=set(REGIONS))
        self.assertIsNone(detailed_relationship("custom bench variation"))
        self.assertIn("side_delt",detailed_relationship("Lateral raises")[0])
    def test_history_and_compare(self):
        today=dt.date(2026,11,17)
        rows=[new_set("2026-11-17","Lateral raise",12,8),new_set("2026-11-16","Shoulder press",8,20),
              new_set("2026-11-15","Bench press",8,60),new_set("2026-11-10","Lateral raise",10,8),
              new_set("2026-11-14","Unknown movement",8,10),new_set("2026-11-18","Lateral raise",12,8)]
        report=region_history(rows,"side_delt",7,today)
        self.assertEqual((report["primary"],report["secondary"],report["sessions"],report["unclassified"]),(2,0,2,1))
        self.assertEqual(report["last_date"],"2026-11-17")
        self.assertEqual(period_comparison(rows,"side_delt",7,today)["primary_change"],1)
    def test_geometry(self):
        for part in PARTS:
            self.assertEqual(len(list(faces(part))),72)
            self.assertTrue(all(math.isfinite(x) for f in faces(part) for p in f for x in p))
        for yaw in (0,90,180,270,360):
            rows=scene(yaw,15,"all")
            self.assertGreater(len(rows),100)
            self.assertEqual([r[0] for r in rows],sorted(r[0] for r in rows))
            self.assertTrue(all(0<=r[3]<=1 for r in rows))
        front=scene(0,0,"surface")
        self.assertNotIn("rhomboids",{r[1] for r in front})
        self.assertIn("rhomboids",{r[1] for r in scene(180,0,"deep")})
        self.assertTrue({r[1] for r in scene(0,0,"all","upper_pec")}<={"","upper_pec"})
        a=rotate((.3,1.4,.5),0);b=rotate((.3,1.4,.5),360)
        for x,y in zip(a,b):self.assertAlmostEqual(x,y)
if __name__=="__main__":unittest.main()
