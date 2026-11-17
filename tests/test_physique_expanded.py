import base64
import datetime as dt
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from cog_core.physique import _crypto
from cog_core.physique_coach import CoachQueue
from cog_core.physique_anatomy import muscle_history, relationship
from cog_core.physique_training import new_set
from cog_core.physique_mobile import snapshot,encode_snapshot,write_snapshot,AAD,ITERATIONS

class ExpandedTests(unittest.TestCase):
    def test_team_gate(self):
        queue=CoachQueue()
        team=queue.create_team("Fictional training and recovery review")
        self.assertEqual(len({m.team for m in team}),1)
        with self.assertRaises(ValueError):queue.synthesize(team[0].id,"safety")
        for m in team:
            queue.attach_response(m.id,"Short educational draft "+m.role)
            queue.decide(m.id,"accepted","Reviewed")
        with self.assertRaises(ValueError):queue.synthesize(team[0].id)
        safety=queue.synthesize(team[0].id,"safety")
        self.assertIn("nutrition",safety.prompt)
        queue.attach_response(safety.id,"No clinical approval; limitations noted")
        queue.decide(safety.id,"accepted","Reviewed")
        commander=queue.synthesize(team[0].id)
        self.assertIn("No clinical approval",commander.prompt)
        self.assertEqual(queue.accepted_feedback(),[])
        queue.attach_response(commander.id,"Educational synthesis")
        queue.decide(commander.id,"accepted","Reviewed")
        self.assertEqual(len(queue.accepted_feedback()),1)
        with self.assertRaises(ValueError):queue.synthesize(team[0].id)
        queue.clear()
        self.assertEqual(queue.accepted_feedback(),[])
    def test_team_isolation_and_rejection(self):
        q=CoachQueue();first=q.create_team("One");second=q.create_team("Two")
        for m in second:
            q.attach_response(m.id,"Draft")
            q.decide(m.id,"accepted","Reviewed")
        with self.assertRaises(ValueError):q.synthesize(first[0].id,"safety")
        q.attach_response(first[0].id,"Unsafe")
        q.decide(first[0].id,"rejected","Do not use")
        with self.assertRaises(ValueError):q.synthesize(first[0].id,"safety")
    def test_muscle_history(self):
        today=dt.date(2026,11,17)
        rows=[new_set("2026-11-17","Bench Press",10,60),new_set("2026-11-16","Triceps extensions",12,10),
              new_set("2026-11-15","Unknown exercise",10,10),new_set("2026-10-01","Bench Press",10,60),
              new_set("2026-11-18","Bench Press",10,60)]
        r=muscle_history(rows,"triceps",today)
        self.assertEqual((r["primary"],r["secondary"],r["unclassified"]),(1,1,1))
        self.assertIsNone(relationship("not a bench press"))
        self.assertEqual(relationship("RDL")[0],("hamstrings","glutes"))
    def test_mobile_encryption(self):
        try:AESGCM,_,InvalidTag=_crypto()
        except ValueError:self.skipTest("cryptography unavailable")
        state={"version":2,"target_date":None,"records":[],"sets":[new_set("2026-11-17","Bench press",10,60),new_set("2026-01-01","Squat",8,70)],"milestones":[]}
        data=snapshot(state,days=30,today=dt.date(2026,11,17))
        self.assertEqual(len(data["sets"]),1)
        password="test-only-mobile-passphrase"
        blob=base64.b64decode(encode_snapshot(data,password))
        self.assertNotIn(b"Bench press",blob)
        key=hashlib.pbkdf2_hmac("sha256",password.encode(),blob[:16],ITERATIONS,dklen=32)
        self.assertEqual(json.loads(AESGCM(key).decrypt(blob[16:28],blob[28:],AAD)),data)
        wrong=hashlib.pbkdf2_hmac("sha256",b"wrong password",blob[:16],ITERATIONS,dklen=32)
        with self.assertRaises(InvalidTag):AESGCM(wrong).decrypt(blob[16:28],blob[28:],AAD)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"snapshot.html"
            write_snapshot(path,data,password)
            html=path.read_text(encoding="utf-8")
            self.assertNotIn("Bench press",html)
            self.assertNotIn(password,html)
            self.assertNotIn("__COG_ENCRYPTED_PAYLOAD__",html)
            with self.assertRaises(FileExistsError):write_snapshot(path,data,password)
if __name__=="__main__":unittest.main()
