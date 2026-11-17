import math
import tempfile
import unittest
import zipfile
from pathlib import Path
from cog_core.physique_atlas import load_region,normalize_mesh,parse_obj,PRESETS
from cog_core.physique_biomechanics import joint_angle,frame,EXERCISES

OBJ=b"v 0 0 0\nv 2 0 0\nv 0 1 0\nv 0 0 3\nf 1 2 3\nf 1 3 4\n"
class AtlasTests(unittest.TestCase):
    def test_obj(self):
        self.assertEqual(len(parse_obj(OBJ)),2)
        self.assertEqual(len(parse_obj(b"v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\nf -4 -3 -2 -1\n")),2)
        for bad in (b"v nan 0 0\n",OBJ+b"f 0 2 3\n",OBJ+b"f 1 2 99\n",b"mtllib remote.mtl\n"):
            with self.assertRaises(ValueError):parse_obj(bad)
    def test_import_and_fit(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);m=p/"isa_element_parts.txt";z=p/"test.zip"
            m.write_text("concept id\tname\telement file id\nFMA34690\tTest right\tFJ1\nFMA34691\tTest left\tFJ2\n",encoding="utf-8")
            with zipfile.ZipFile(z,"w") as f:
                f.writestr("nested/FJ1.obj",OBJ)
                f.writestr("FJ2.obj",OBJ)
                f.writestr("../../unused.txt","ignored")
            result=load_region(z,m,PRESETS["Upper pectorals"])
            self.assertEqual(result["triangle_count"],4)
            self.assertEqual(len(result["metadata_sha256"]),64)
            meshes=normalize_mesh(result["meshes"])
            pts=[v for _,tris in meshes for t in tris for v in t]
            self.assertTrue(all(abs(x)<=.500001 for v in pts for x in v))
            with self.assertRaises(ValueError):load_region(z,m,["FMA999"])
            with zipfile.ZipFile(z,"a") as f:f.writestr("another/FJ1.obj",OBJ)
            with self.assertRaises(ValueError):load_region(z,m,PRESETS["Upper pectorals"])
            self.assertEqual(sorted(x.name for x in p.iterdir()),["isa_element_parts.txt","test.zip"])
    def test_angle(self):
        self.assertAlmostEqual(joint_angle((1,0),(0,0),(0,1)),90)
        self.assertAlmostEqual(joint_angle((1,0,0),(0,0,0),(-1,0,0)),180)
        self.assertAlmostEqual(joint_angle((1,0),(0,0),(2,0)),0)
        with self.assertRaises(ValueError):joint_angle((0,0),(0,0),(1,1))
    def test_animation(self):
        for name in EXERCISES:
            start=frame(name,0);mid=frame(name,.5);end=frame(name,1)
            self.assertEqual(start["points"],end["points"])
            self.assertNotEqual(start["points"],mid["points"])
            for k in range(21):
                f=frame(name,k/20)
                self.assertTrue(all(0<=x<=180 for x in f["angles"].values()))
                p=f["points"]
                for a,b,l in (("ankle","knee",.43),("knee","hip",.43),("hip","shoulder",.52),("shoulder","elbow",.30),("elbow","wrist",.27)):
                    self.assertAlmostEqual(math.dist(p[a],p[b]),l)
        self.assertAlmostEqual(frame("Biceps curl",0)["angles"]["elbow"],180)
        self.assertAlmostEqual(frame("Biceps curl",.5)["angles"]["elbow"],45)
        self.assertAlmostEqual(frame("Squat",.5)["angles"]["knee"],90)
if __name__=="__main__":unittest.main()
