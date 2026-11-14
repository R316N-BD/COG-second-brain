from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from cog_core import cli, semantic

class SemanticTests(unittest.TestCase):
    def test_scope_ranking_and_stale_suppression(self):
        with tempfile.TemporaryDirectory() as tmp:
            data=cli.init_vault(Path(tmp)/"data")
            a=data/"vault/04-projects/a.md"
            a.write_text("alpha",encoding="utf-8")
            (data/"vault/04-projects/b.md").write_text("beta",encoding="utf-8")
            (data/"vault/02-personal/secret.md").write_text("secret",encoding="utf-8")
            def embed(model,inputs):
                self.assertNotIn("secret",inputs)
                return [[1.0,0.0] if x=="alpha" else [0.0,1.0] for x in inputs]
            model="embeddinggemma:latest"
            with patch.object(semantic,"_embed",side_effect=embed):
                self.assertEqual(semantic.build(data,"04-projects",model)["indexed"],2)
                r=semantic.search(data,"04-projects",model,"alpha")
                self.assertEqual(r["results"][0]["path"],"04-projects/a.md")
                a.write_text("changed",encoding="utf-8")
                self.assertEqual(len(semantic.search(data,"04-projects",model,"alpha")["results"]),1)
    def test_invalid_vector(self):
        for v in ([0,0],[float("nan")],[True]):
            with self.assertRaises(ValueError):
                semantic._normalized(v)
