import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "master-interviewer" / "scripts" / "progress_tracker.py"
CATALOG = ROOT / "examples" / "catalog.example.json"


class ProgressTrackerTest(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_init_mark_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_option = ("--state-dir", temp_dir)

            self.run_cli(
                *state_option,
                "init",
                "--profile",
                "demo",
                "--candidate",
                "Demo User",
                "--role",
                "Backend Engineer",
                "--catalog",
                str(CATALOG),
            )
            self.run_cli(
                *state_option,
                "mark-asked",
                "--profile",
                "demo",
                "--topic-id",
                "database-range-lock",
                "--mode",
                "coverage",
                "--question",
                "范围锁解决什么问题？",
            )
            self.run_cli(
                *state_option,
                "mark-result",
                "--profile",
                "demo",
                "--topic-id",
                "database-range-lock",
                "--grade",
                "C",
                "--weakness",
                "知道现象，但没有说明锁定范围",
            )

            state = json.loads((Path(temp_dir) / "demo.json").read_text(encoding="utf-8"))
            topic = next(
                item for item in state["topics"] if item["topic_id"] == "database-range-lock"
            )
            self.assertEqual(topic["interview_count"], 1)
            self.assertEqual(topic["mastery"], "C")

            report = self.run_cli(*state_option, "report", "--profile", "demo")
            self.assertIn("数据库范围锁", report.stdout)


if __name__ == "__main__":
    unittest.main()
