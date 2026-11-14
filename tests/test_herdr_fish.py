"""Exercise the actual Fish PWD handler with a controlled Herdr CLI."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


FISH = shutil.which("fish")
HOOK = Path(__file__).resolve().parents[1] / "dotfiles/.config/fish/conf.d/herdr-auto-space.fish"


@unittest.skipUnless(FISH and shutil.which("git") and shutil.which("jq"), "requires Fish, Git, and jq")
class HerdrFishTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        (self.project / "nested").mkdir()
        subprocess.run(["git", "init", "--quiet", str(self.project)], check=True)
        self.record = self.root / "calls.jsonl"
        self.fake = self.root / "herdr"
        self.fake.write_text(f"#!{sys.executable}\n" + '''
import json, os, sys
args = sys.argv[1:]
with open(os.environ["TEST_HERDR_RECORD"], "a") as f:
    f.write(json.dumps(args) + "\\n")
mode = os.environ.get("TEST_HERDR_MODE", "ok")
if mode == "failure":
    print("server unavailable", file=sys.stderr)
    sys.exit(1)
if mode == "malformed":
    print("invalid JSON")
elif args[:2] == ["pane", "get"]:
    print(json.dumps({"result": {"pane": {"terminal_id": "terminal"}}}))
elif args == ["api", "snapshot"]:
    print(os.environ["TEST_HERDR_SNAPSHOT"])
else:
    print(json.dumps({"result": {"type": "pane_moved"}}))
''')
        self.fake.chmod(0o755)
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("HERDR_")}
        self.env.update(HERDR_PANE_ID="old:alias", HERDR_BIN_PATH=str(self.fake),
                        TEST_HERDR_RECORD=str(self.record), TEST_HERDR_HOOK=str(HOOK),
                        TEST_HERDR_DESTINATION=str(self.project / "nested"))
        self.pane = dict(pane_id="w1:p2", terminal_id="terminal", tab_id="w1:t1", workspace_id="w1")
        self.panes = [self.pane]
        self.workspaces = [dict(workspace_id="w2", label=self.project.name)]

    def run_hook(self):
        self.env["TEST_HERDR_SNAPSHOT"] = json.dumps({"result": {"snapshot": {
            "panes": self.panes, "workspaces": self.workspaces}}})
        result = subprocess.run([str(FISH), "--no-config", "-c",
            'source "$TEST_HERDR_HOOK"; source "$TEST_HERDR_HOOK"; '
            'builtin cd "$TEST_HERDR_DESTINATION"; printf "%s\\n" $status'],
            env=self.env, cwd=self.root, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "0\n")
        self.assertEqual(result.stderr, "")
        return [json.loads(line) for line in self.record.read_text().splitlines()] if self.record.exists() else []

    def test_cd_moves_resolved_pane_once_after_resourcing(self):
        calls = self.run_hook()
        self.assertEqual(calls, [["pane", "get", "old:alias"], ["api", "snapshot"],
            ["pane", "move", "w1:p2", "--new-tab", "--workspace", "w2", "--focus"]])

    def test_creates_missing_space_with_space_in_name(self):
        self.workspaces = []
        self.assertEqual(self.run_hook()[-1], ["pane", "move", "w1:p2", "--new-workspace",
            "--label", self.project.name, "--focus"])

    def test_missing_herdr_is_silent(self):
        self.env["HERDR_BIN_PATH"] = str(self.root / "missing-herdr")
        self.assertEqual(self.run_hook(), [])

    def test_non_git_directory_creates_space(self):
        destination = self.root / "ordinary directory" / "nested directory"
        destination.mkdir(parents=True)
        self.env["TEST_HERDR_DESTINATION"] = str(destination)
        self.assertEqual(self.run_hook()[-1], ["pane", "move", "w1:p2", "--new-workspace",
            "--label", destination.name, "--focus"])

    def test_without_git_uses_current_directory(self):
        binary_dir = self.root / "bin"
        binary_dir.mkdir()
        (binary_dir / "jq").symlink_to(str(shutil.which("jq")))
        self.env["PATH"] = str(binary_dir)
        self.assertEqual(self.run_hook()[-1], ["pane", "move", "w1:p2", "--new-workspace",
            "--label", "nested", "--focus"])

    def test_outside_herdr_is_silent(self):
        del self.env["HERDR_PANE_ID"]
        self.assertEqual(self.run_hook(), [])

    def test_opt_out_is_silent(self):
        self.env["HERDR_AUTO_SPACE_DISABLE"] = "1"
        self.assertEqual(self.run_hook(), [])

    def test_missing_dependencies_are_silent(self):
        self.env["PATH"] = str(self.root)
        self.assertEqual(self.run_hook(), [])

    def test_failure_and_invalid_json_preserve_cd(self):
        for mode in ("failure", "malformed"):
            with self.subTest(mode=mode):
                self.env["TEST_HERDR_MODE"] = mode
                self.run_hook()

    def test_skips_split_tabs_duplicate_labels_and_current_space(self):
        for case in ("split", "duplicate", "current"):
            with self.subTest(case=case):
                self.record.unlink(missing_ok=True)
                self.panes = [self.pane]
                self.workspaces = [dict(workspace_id="w2", label=self.project.name)]
                if case == "split":
                    self.panes.append(dict(self.pane, terminal_id="other", pane_id="w1:p3"))
                elif case == "duplicate":
                    self.workspaces.append(dict(workspace_id="w3", label=self.project.name))
                else:
                    self.workspaces[0]["workspace_id"] = "w1"
                self.assertFalse(any(call[:2] == ["pane", "move"] for call in self.run_hook()))


if __name__ == "__main__":
    unittest.main()
