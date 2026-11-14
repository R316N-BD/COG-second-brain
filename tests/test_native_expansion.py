import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from cog_core import cli, expansion, research_lab, document_ingest

class ExpansionTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root=cli.init_vault(Path(t.name)/"data")
        self.folder=Path(t.name)

    def test_catalog_has_all_modules(self):
        rows=expansion.catalog()
        self.assertEqual(len(rows),20)
        self.assertEqual(len({r["id"] for r in rows}),20)

    def test_workflow_dependency_order_and_history(self):
        doc={"name":"Test","nodes":[
            {"id":"graph","action":"graph","after":["index"]},
            {"id":"index","action":"index","after":[]}]}
        self.assertEqual([n["id"] for n in expansion.validate_workflow(doc)],["index","graph"])
        result=expansion.run_workflow(self.root,doc)
        self.assertEqual(result["status"],"completed")
        self.assertEqual(expansion.history(self.root)[0]["status"],"completed")

    def test_reject_cycles_and_shell(self):
        for nodes in ([{"id":"a","action":"graph","after":["a"]}],
                      [{"id":"a","action":"shell","after":[]}],
                      [{"id":"a","action":"graph","after":["missing"]}]):
            with self.assertRaises(ValueError):
                expansion.validate_workflow({"name":"Invalid","nodes":nodes})

    def test_failed_workflow_is_recorded(self):
        doc={"name":"Failure","nodes":[{"id":"a","action":"graph","after":[]}]}
        with patch.object(expansion.graph,"build",side_effect=ValueError("test failure")):
            with self.assertRaises(ValueError):
                expansion.run_workflow(self.root,doc)
        self.assertEqual(expansion.history(self.root)[0]["status"],"failed")

    def test_ingest_is_create_only(self):
        source=self.folder/"sample.txt"
        source.write_text("Test note",encoding="utf-8")
        result=document_ingest.ingest(self.root,source)
        note=self.root/"vault"/result["path"]
        self.assertIn("Test note",note.read_text(encoding="utf-8"))
        with self.assertRaises(FileExistsError):
            document_ingest.ingest(self.root,source)

    def test_backtest_no_lookahead_and_fees(self):
        path=self.folder/"prices.csv"
        path.write_text("close\n100\n110\n121\n",encoding="utf-8")
        r=research_lab.backtest(path,2,10)
        self.assertAlmostEqual(r["return_pct"],100*(1.1*.999*.999-1))
        self.assertEqual(r["position_changes"],2)
        path.write_text("close\n1\nnan\n3\n",encoding="utf-8")
        with self.assertRaises(ValueError):
            research_lab.backtest(path,2)

    def test_backtest_flat_series(self):
        path=self.folder/"flat.csv"
        path.write_text("close\n10\n10\n10\n10\n",encoding="utf-8")
        self.assertEqual(research_lab.backtest(path,2)["return_pct"],0)
