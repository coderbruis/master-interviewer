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
            self.assertEqual(state["schema_version"], 2)
            self.assertEqual(state["interview_config"]["company_style"], "jd")

            report = self.run_cli(*state_option, "report", "--profile", "demo")
            self.assertIn("数据库范围锁", report.stdout)
            self.assertIn("京东风格", report.stdout)

    def test_set_show_config_and_question_history(self) -> None:
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

            changed = self.run_cli(
                *state_option,
                "set-config",
                "--profile",
                "demo",
                "--strategy",
                "coverage",
                "--style",
                "bytedance",
            )
            self.assertIn("查漏补缺模式｜字节风格", changed.stdout)
            self.assertIn("$master-interviewer 字节风格 查漏补缺", changed.stdout)

            shown = self.run_cli(
                *state_option, "show-config", "--profile", "demo"
            )
            self.assertEqual(changed.stdout, shown.stdout)

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
            state = json.loads((Path(temp_dir) / "demo.json").read_text(encoding="utf-8"))
            topic = next(
                item for item in state["topics"] if item["topic_id"] == "database-range-lock"
            )
            self.assertEqual(topic["history"][-1]["company_style"], "bytedance")

    def test_legacy_profile_gets_default_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state = {
                "schema_version": 1,
                "profile_id": "legacy",
                "candidate": "Legacy User",
                "target_role": "Backend Engineer",
                "created_at": "2026-01-01T00:00:00+08:00",
                "updated_at": "2026-01-01T00:00:00+08:00",
                "topics": [],
            }
            (Path(temp_dir) / "legacy.json").write_text(
                json.dumps(state, ensure_ascii=False), encoding="utf-8"
            )

            shown = self.run_cli(
                "--state-dir", temp_dir, "show-config", "--profile", "legacy"
            )
            self.assertIn("面试官模式｜深挖模式｜京东风格", shown.stdout)


if __name__ == "__main__":
    unittest.main()
