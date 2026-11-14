import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(*args, cwd, check=True):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode:
        raise AssertionError(f"{args!r} exited {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result

def git(cwd, *args, **kw):
    return run("git", *args, cwd=cwd, **kw)

def init(repo):
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "COG Test")

def write(root, path, content):
    file = root / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")

def commit(repo):
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "fixture")

class HardeningTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.tmp = Path(temp.name)

    def test_ignore_private_data(self):
        repo = self.tmp / "repo"
        init(repo)
        shutil.copy(ROOT / ".gitignore", repo / ".gitignore")
        for path in ["00-inbox/MY-PROFILE.md", "01-daily/journal/note.md",
                     "02-personal/secret.md", "03-professional/note.md",
                     "04-projects/work/notes.md", "05-knowledge/notes.md",
                     "06-templates/private.md", ".env.local", "secret.pem",
                     "file.md.backup-20261114", "runtime/data.sqlite"]:
            with self.subTest(path=path):
                self.assertEqual(git(repo, "check-ignore", "-q", "--no-index", path, check=False).returncode, 0)
        self.assertEqual(git(repo, "check-ignore", "-q", "--no-index", "README.md", check=False).returncode, 1)

    def test_checkpoint(self):
        script = self.tmp / ".claude/lib/checkpoint.sh"
        script.parent.mkdir(parents=True)
        shutil.copy(ROOT / ".claude/lib/checkpoint.sh", script)
        target = self.tmp / "run"
        for cp, status in [("CP-99", "PASS"), ("CP-1", "BOGUS")]:
            result = run("bash", str(script), "record", str(target), cp, status, "test", cwd=self.tmp, check=False)
            self.assertNotEqual(result.returncode, 0)
        self.assertFalse(target.exists())
        run("bash", str(script), "record", str(target), "CP-1", "PASS", "one\ttwo\nthree\\n", cwd=self.tmp)
        rows = (target / "evidence/checkpoints.tsv").read_text().splitlines()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].split("\t")[1:], ["CP-1", "PASS", "one two three\\n"])

    def fixture(self, validator_exit=0):
        upstream = self.tmp / "upstream"
        init(upstream)
        for p, data in [("COG-VERSION", "2\n"), ("AGENTS.md", "new agents\n"),
                        ("CHANGELOG.md", "new changelog\n"), (".gitignore", "# unsafe\n")]:
            write(upstream, p, data)
        commit(upstream)
        local = self.tmp / "local"
        init(local)
        source = (ROOT / "cog-update.sh").read_text()
        source = source.replace("https://github.com/huytieu/COG-second-brain.git", str(upstream))
        write(local, "cog-update.sh", source)
        shutil.copy(ROOT / ".gitignore", local / ".gitignore")
        write(local, "COG-VERSION", "1\n")
        write(local, "AGENTS.md", "old agents\n")
        write(local, "CHANGELOG.md", "old changelog\n")
        write(local, "scripts/build-agent-plugin.sh", "#!/bin/bash\nexit 0\n")
        write(local, "scripts/validate-agent-surface.sh", f"#!/bin/bash\nexit {validator_exit}\n")
        commit(local)
        write(local, "00-inbox/MY-PROFILE.md", "private\n")
        return local

    def test_force_multiple_files_and_privacy(self):
        local = self.fixture()
        original_ignore = (local / ".gitignore").read_text()
        result = run("bash", str(local / "cog-update.sh"), "--force", cwd=self.tmp)
        self.assertIn("Updated 3 file(s)", result.stdout)
        self.assertEqual((local / "AGENTS.md").read_text(), "new agents\n")
        self.assertEqual((local / "CHANGELOG.md").read_text(), "new changelog\n")
        self.assertEqual((local / ".gitignore").read_text(), original_ignore)
        self.assertEqual((local / "00-inbox/MY-PROFILE.md").read_text(), "private\n")
        self.assertEqual(len(list(local.glob("AGENTS.md.backup-*"))), 1)

    def test_validation_failure(self):
        local = self.fixture(validator_exit=7)
        result = run("bash", "cog-update.sh", "--force", cwd=local, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("Updated 3 file(s) from upstream", result.stdout)

    def test_dirty_tree_refused(self):
        local = self.fixture()
        write(local, "AGENTS.md", "local changes\n")
        result = run("bash", "cog-update.sh", "--force", cwd=local, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((local / "AGENTS.md").read_text(), "local changes\n")

    def test_dry_run(self):
        local = self.fixture()
        run("bash", "cog-update.sh", "--dry-run", cwd=local)
        self.assertEqual((local / "AGENTS.md").read_text(), "old agents\n")
        self.assertFalse(list(local.glob("*.backup-*")))
