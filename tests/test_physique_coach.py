import unittest
from cog_core.physique_coach import CoachQueue, ROLES, build_prompt

class CoachTests(unittest.TestCase):
    def test_roles(self):
        self.assertEqual(len(ROLES),7)
        for role,(title,scope) in ROLES.items():
            prompt=build_prompt(role,"Review a fictional example.")
            self.assertIn(title,prompt)
            self.assertIn(scope,prompt)
            self.assertIn("Do not access files",prompt)
            self.assertIn("Never mark your own draft approved",prompt)
    def test_validation(self):
        for task in ("", " "*5, "x"*6001, "\x00"):
            with self.assertRaises(ValueError):build_prompt("training",task)
        with self.assertRaises(ValueError):build_prompt("unknown","example")
    def test_review(self):
        q=CoachQueue();m=q.create("training","Review a fictional program.")
        self.assertEqual(m.state,"draft")
        q.staged(m.id)
        with self.assertRaises(ValueError):q.staged(m.id)
        with self.assertRaises(ValueError):q.decide(m.id,"accepted","too early")
        q.attach_response(m.id,"Draft observations")
        self.assertEqual(m.state,"awaiting_review")
        q.decide(m.id,"accepted","Educational draft reviewed")
        self.assertEqual(m.state,"accepted")
        with self.assertRaises(ValueError):q.attach_response(m.id,"New response")
        q.clear()
        with self.assertRaises(ValueError):q.get(m.id)
    def test_reject_and_limits(self):
        q=CoachQueue();m=q.create("safety","Review a hypothetical draft.")
        with self.assertRaises(ValueError):q.attach_response(m.id,"x"*24001)
        q.attach_response(m.id,"Insufficient evidence")
        q.decide(m.id,"rejected","Missing support")
        self.assertEqual(m.state,"rejected")
        for _ in range(39):q.create("research","Review general evidence")
        with self.assertRaises(ValueError):q.create("research","Queue full")

if __name__=="__main__":unittest.main()
