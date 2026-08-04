#!/usr/bin/env python3
"""Persist interview coverage, mastery, and review state."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


PROFILE_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,79}$")
DEFAULT_STATE_DIR = Path.home() / ".codex" / "master-interviewer-state"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def state_path(profile: str, state_dir: Path) -> Path:
    if not PROFILE_RE.fullmatch(profile):
        raise SystemExit("profile must contain only lowercase letters, digits, and hyphens")
    return state_dir / f"{profile}.json"


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"state does not exist: {path}")
    with path.open("r", encoding="utf-8") as handle:
        state = json.load(handle)
    for topic in state.get("topics", []):
        ensure_review_fields(topic)
    return state


def ensure_review_fields(topic: dict[str, Any]) -> None:
    """Add review fields lazily so existing profile files remain compatible."""
    if "focus_level" not in topic:
        mastery = topic.get("mastery")
        if mastery == "D":
            topic["focus_level"] = 3
        elif mastery == "C" or (mastery == "B" and topic.get("hint_used")):
            topic["focus_level"] = 2
        elif mastery == "B":
            topic["focus_level"] = 1
        else:
            topic["focus_level"] = 0
    topic.setdefault("focus_reason", topic.get("weakness", ""))
    topic.setdefault("wrong_count", 0)
    topic.setdefault("review_count", 0)
    topic.setdefault("correct_streak", 0)
    topic.setdefault("last_reviewed_at", None)
    topic.setdefault("last_question_was_review", False)
    if "correction_count" not in topic:
        topic["correction_count"] = sum(
            item.get("type") == "result" and item.get("grade") in {"B", "C", "D"}
            for item in topic.get("history", [])
        )
    topic.setdefault(
        "needs_correction",
        topic.get("mastery") in {"B", "C", "D"} or topic["focus_level"] > 0,
    )
    topic.setdefault(
        "correction_reason", topic.get("focus_reason") or topic.get("weakness", "")
    )
    topic.setdefault("correction_resolved_at", None)


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.stem}-", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def load_catalog(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    topics = payload.get("topics") if isinstance(payload, dict) else payload
    if not isinstance(topics, list):
        raise SystemExit("catalog must be a JSON list or an object containing a topics list")
    required = {"topic_id", "label", "kind", "domain", "project", "source"}
    seen: set[str] = set()
    for topic in topics:
        missing = required - set(topic)
        if missing:
            raise SystemExit(f"catalog topic missing fields {sorted(missing)}: {topic}")
        topic_id = topic["topic_id"]
        if not isinstance(topic_id, str) or not PROFILE_RE.fullmatch(topic_id):
            raise SystemExit(f"invalid topic_id: {topic_id}")
        if topic_id in seen:
            raise SystemExit(f"duplicate topic_id: {topic_id}")
        seen.add(topic_id)
    return topics


def normalized_topic(topic: dict[str, Any]) -> dict[str, Any]:
    return {
        "topic_id": topic["topic_id"],
        "label": topic["label"],
        "kind": topic["kind"],
        "domain": topic["domain"],
        "project": topic["project"],
        "source": topic["source"],
        "active": topic.get("active", True),
        "interview_count": 0,
        "followup_count": 0,
        "last_asked_at": None,
        "last_result_at": None,
        "mastery": None,
        "hint_used": False,
        "weakness": "",
        "focus_level": 0,
        "focus_reason": "",
        "wrong_count": 0,
        "review_count": 0,
        "correct_streak": 0,
        "last_reviewed_at": None,
        "last_question_was_review": False,
        "needs_correction": False,
        "correction_count": 0,
        "correction_reason": "",
        "correction_resolved_at": None,
        "history": [],
    }


def merge_catalog(state: dict[str, Any], topics: list[dict[str, Any]]) -> None:
    existing = {topic["topic_id"]: topic for topic in state["topics"]}
    incoming_ids = set()
    for catalog_topic in topics:
        topic_id = catalog_topic["topic_id"]
        incoming_ids.add(topic_id)
        if topic_id not in existing:
            state["topics"].append(normalized_topic(catalog_topic))
            continue
        saved = existing[topic_id]
        for field in ("label", "kind", "domain", "project", "source"):
            saved[field] = catalog_topic[field]
        saved["active"] = catalog_topic.get("active", True)
    for topic in state["topics"]:
        if topic["source"] == "resume" and topic["topic_id"] not in incoming_ids:
            topic["active"] = False


def find_topic(state: dict[str, Any], topic_id: str) -> dict[str, Any]:
    for topic in state["topics"]:
        if topic["topic_id"] == topic_id:
            return topic
    raise SystemExit(f"unknown topic_id: {topic_id}")


def state_dir_from(args: argparse.Namespace) -> Path:
    return Path(args.state_dir).expanduser()


def command_init(args: argparse.Namespace) -> None:
    path = state_path(args.profile, state_dir_from(args))
    topics = load_catalog(Path(args.catalog))
    if path.exists():
        state = load_state(path)
        merge_catalog(state, topics)
        state["candidate"] = args.candidate
        state["target_role"] = args.role
    else:
        state = {
            "schema_version": 1,
            "profile_id": args.profile,
            "candidate": args.candidate,
            "target_role": args.role,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "topics": [normalized_topic(topic) for topic in topics],
        }
    state["updated_at"] = now_iso()
    atomic_write(path, state)
    print(path)


def command_mark_asked(args: argparse.Namespace) -> None:
    path = state_path(args.profile, state_dir_from(args))
    state = load_state(path)
    topic = find_topic(state, args.topic_id)
    timestamp = now_iso()
    is_review = topic["focus_level"] > 0
    topic["interview_count"] += 1
    topic["last_asked_at"] = timestamp
    topic["last_question_was_review"] = is_review
    if is_review:
        topic["review_count"] += 1
        topic["last_reviewed_at"] = timestamp
    topic["history"].append(
        {
            "type": "question",
            "at": timestamp,
            "mode": args.mode,
            "summary": args.question,
            "review": is_review,
            "focus_level": topic["focus_level"],
        }
    )
    state["updated_at"] = timestamp
    atomic_write(path, state)
    print(f"{topic['label']}\t{topic['interview_count']}")


def command_mark_followup(args: argparse.Namespace) -> None:
    path = state_path(args.profile, state_dir_from(args))
    state = load_state(path)
    topic = find_topic(state, args.topic_id)
    timestamp = now_iso()
    topic["followup_count"] += 1
    topic["history"].append(
        {"type": "followup", "at": timestamp, "summary": args.question}
    )
    state["updated_at"] = timestamp
    atomic_write(path, state)
    print(f"{topic['label']}\tfollowups={topic['followup_count']}")


def command_mark_result(args: argparse.Namespace) -> None:
    path = state_path(args.profile, state_dir_from(args))
    state = load_state(path)
    topic = find_topic(state, args.topic_id)
    timestamp = now_iso()
    topic["mastery"] = args.grade
    topic["hint_used"] = args.hint_used
    topic["weakness"] = args.weakness
    topic["last_result_at"] = timestamp
    if args.grade == "D":
        topic["focus_level"] = 3
        topic["focus_reason"] = args.weakness or "核心问题回答错误或不了解"
        topic["wrong_count"] += 1
        topic["correct_streak"] = 0
    elif args.grade == "C":
        topic["focus_level"] = max(topic["focus_level"], 2)
        topic["focus_reason"] = args.weakness or "仅了解概念，缺少原理或应用能力"
        topic["wrong_count"] += 1
        topic["correct_streak"] = 0
    elif args.grade == "B":
        minimum_level = 2 if args.hint_used else 1
        topic["focus_level"] = max(topic["focus_level"], minimum_level)
        topic["focus_reason"] = args.weakness or "结论正确，但原理或边界不足"
        topic["correct_streak"] = 0
    elif topic["last_question_was_review"] and topic["focus_level"] > 0:
        topic["correct_streak"] += 1
        if topic["correct_streak"] >= 2:
            topic["focus_level"] -= 1
            topic["correct_streak"] = 0
            if topic["focus_level"] == 0:
                topic["focus_reason"] = ""
    if args.grade in {"B", "C", "D"}:
        topic["needs_correction"] = True
        topic["correction_count"] += 1
        topic["correction_reason"] = args.weakness or topic["focus_reason"]
        topic["correction_resolved_at"] = None
    elif topic["focus_level"] == 0:
        topic["needs_correction"] = False
        topic["correction_reason"] = ""
        if topic["correction_count"] > 0:
            topic["correction_resolved_at"] = timestamp
    else:
        topic["needs_correction"] = True
    topic["history"].append(
        {
            "type": "result",
            "at": timestamp,
            "grade": args.grade,
            "hint_used": args.hint_used,
            "weakness": args.weakness,
            "focus_level": topic["focus_level"],
            "correct_streak": topic["correct_streak"],
            "needs_correction": topic["needs_correction"],
            "correction_count": topic["correction_count"],
        }
    )
    state["updated_at"] = timestamp
    atomic_write(path, state)
    print(f"{topic['label']}\t{args.grade}")


def command_mark_focus(args: argparse.Namespace) -> None:
    path = state_path(args.profile, state_dir_from(args))
    state = load_state(path)
    topic = find_topic(state, args.topic_id)
    timestamp = now_iso()
    topic["focus_level"] = max(topic["focus_level"], args.level)
    topic["focus_reason"] = args.reason
    topic["correct_streak"] = 0
    topic["needs_correction"] = True
    topic["correction_reason"] = args.reason
    topic["correction_resolved_at"] = None
    topic["history"].append(
        {
            "type": "focus",
            "at": timestamp,
            "level": topic["focus_level"],
            "reason": args.reason,
        }
    )
    state["updated_at"] = timestamp
    atomic_write(path, state)
    print(f"{topic['label']}\tfocus={topic['focus_level']}")


def command_report(args: argparse.Namespace) -> None:
    path = state_path(args.profile, state_dir_from(args))
    state = load_state(path)
    active = [topic for topic in state["topics"] if topic.get("active", True)]
    if args.focus_only:
        focused = sorted(
            (topic for topic in active if topic["focus_level"] > 0),
            key=lambda topic: (-topic["focus_level"], topic["last_reviewed_at"] or ""),
        )
        labels = {3: "重点拷问", 2: "重点复习", 1: "持续观察"}
        print(f"profile: {state['profile_id']}")
        print(f"focused: {len(focused)}")
        for topic in focused:
            print(
                f"- [{labels[topic['focus_level']]}] {topic['label']}: "
                f"复习 {topic['review_count']} 次; 掌握度 {topic['mastery'] or '-'}; "
                f"连续答对 {topic['correct_streak']}/2; "
                f"需要修正 {'是' if topic['needs_correction'] else '否'}; "
                f"原因 {topic['focus_reason'] or '-'}"
            )
        return
    covered = [topic for topic in active if topic["interview_count"] > 0]
    if args.json:
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return
    percentage = 0 if not active else round(len(covered) * 100 / len(active), 1)
    print(f"profile: {state['profile_id']}")
    print(f"coverage: {len(covered)}/{len(active)} ({percentage}%)")
    focus_counts = {
        level: sum(topic["focus_level"] == level for topic in active)
        for level in (3, 2, 1)
    }
    print(
        "focus: "
        f"重点拷问 {focus_counts[3]}; 重点复习 {focus_counts[2]}; "
        f"持续观察 {focus_counts[1]}"
    )
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for topic in active:
        groups.setdefault((topic["project"] or "通用技术", topic["domain"]), []).append(topic)
    for (project, domain), topics in sorted(groups.items()):
        print(f"\n[{project} / {domain}]")
        for topic in topics:
            status = (
                f"已面试 {topic['interview_count']} 次"
                if topic["interview_count"]
                else "0 次（未面试）"
            )
            mastery = topic["mastery"] or "-"
            focus = {3: "重点拷问", 2: "重点复习", 1: "持续观察"}.get(
                topic["focus_level"], "-"
            )
            correction = "需要修正" if topic["needs_correction"] else "-"
            print(
                f"- {topic['label']}: {status}; 掌握度 {mastery}; "
                f"重点 {focus}; 修正 {correction}"
            )


def progress_bar(current: int, total: int, width: int = 16) -> str:
    """Return a compact, deterministic text progress bar."""
    if total <= 0:
        return "░" * width
    filled = round(current * width / total)
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def command_dashboard(args: argparse.Namespace) -> None:
    """Print a read-only Markdown dashboard for coverage and mastery."""
    path = state_path(args.profile, state_dir_from(args))
    state = load_state(path)
    active = [topic for topic in state["topics"] if topic.get("active", True)]
    covered = [topic for topic in active if topic["interview_count"] > 0]
    evaluated = [topic for topic in active if topic.get("mastery")]
    focused = [topic for topic in active if topic["focus_level"] > 0]
    reviewed = [topic for topic in active if topic["review_count"] > 0]
    resolved_reviews = [
        topic
        for topic in active
        if topic["review_count"] > 0 and topic["focus_level"] == 0
    ]
    pending_corrections = [topic for topic in active if topic["needs_correction"]]
    correction_attempts = sum(topic["correction_count"] for topic in active)
    resolved_corrections = [
        topic
        for topic in active
        if topic["correction_count"] > 0 and not topic["needs_correction"]
    ]

    total = len(active)
    coverage_percentage = 0 if not total else len(covered) * 100 / total
    mastery_counts = {
        grade: sum(topic.get("mastery") == grade for topic in active)
        for grade in ("A", "B", "C", "D")
    }
    focus_counts = {
        level: sum(topic["focus_level"] == level for topic in active)
        for level in (3, 2, 1)
    }

    print(f"# {state['candidate']}｜{state['target_role']}面试进度")
    print()
    print(f"- 更新时间：{state['updated_at']}")
    print(
        f"- 总体覆盖：`{progress_bar(len(covered), total)}` "
        f"{len(covered)}/{total}（{coverage_percentage:.1f}%）"
    )
    print(
        f"- 掌握分布：A {mastery_counts['A']}｜B {mastery_counts['B']}｜"
        f"C {mastery_counts['C']}｜D {mastery_counts['D']}｜"
        f"未评估 {total - len(evaluated)}"
    )
    print(
        f"- 重点复习：重点拷问 {focus_counts[3]}｜重点复习 {focus_counts[2]}｜"
        f"持续观察 {focus_counts[1]}"
    )
    print(
        f"- 复习进度：已复习 {len(reviewed)} 个知识点｜"
        f"已移出重点队列 {len(resolved_reviews)} 个知识点"
    )
    print(
        f"- 修正指标：待修正 {len(pending_corrections)} 个知识点｜"
        f"累计非完全正确 {correction_attempts} 次｜"
        f"已完成修正 {len(resolved_corrections)} 个知识点"
    )

    print()
    print("## 领域进度图")
    print()
    print("| 领域 | 进度 | 覆盖 | A/B/C/D/未评估 | 重点题 | 待修正 |")
    print("|---|---:|---:|---:|---:|---:|")
    domains: dict[str, list[dict[str, Any]]] = {}
    for topic in active:
        domains.setdefault(topic["domain"], []).append(topic)
    for domain, topics in sorted(domains.items()):
        domain_covered = sum(topic["interview_count"] > 0 for topic in topics)
        counts = {
            grade: sum(topic.get("mastery") == grade for topic in topics)
            for grade in ("A", "B", "C", "D")
        }
        domain_evaluated = sum(topic.get("mastery") is not None for topic in topics)
        domain_focused = sum(topic["focus_level"] > 0 for topic in topics)
        domain_corrections = sum(topic["needs_correction"] for topic in topics)
        print(
            f"| {domain} | `{progress_bar(domain_covered, len(topics), 10)}` | "
            f"{domain_covered}/{len(topics)} | "
            f"{counts['A']}/{counts['B']}/{counts['C']}/{counts['D']}/"
            f"{len(topics) - domain_evaluated} | {domain_focused} | "
            f"{domain_corrections} |"
        )

    print()
    print("## 每个知识点的掌握程度")
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for topic in active:
        groups.setdefault((topic["project"] or "通用技术", topic["domain"]), []).append(
            topic
        )
    focus_labels = {3: "重点拷问", 2: "重点复习", 1: "持续观察", 0: "-"}
    for (project, domain), topics in sorted(groups.items()):
        print()
        print(f"### {project} / {domain}")
        print()
        print(
            "| 知识点 | 面试次数 | 掌握度 | 修正状态 | 重点状态 | "
            "复习次数 | 薄弱点 |"
        )
        print("|---|---:|---:|---|---|---:|---|")
        for topic in topics:
            weakness = (topic.get("weakness") or "-").replace("|", "\\|")
            if topic["needs_correction"]:
                correction_status = "**需要修正**"
            elif topic["correction_count"] > 0:
                correction_status = "已修正"
            else:
                correction_status = "-"
            print(
                f"| {topic['label']} | {topic['interview_count']} | "
                f"{topic.get('mastery') or '未评估'} | "
                f"{correction_status} | "
                f"{focus_labels[topic['focus_level']]} | "
                f"{topic['review_count']} | {weakness} |"
            )


def command_reset(args: argparse.Namespace) -> None:
    if not args.yes:
        raise SystemExit("reset requires --yes after user confirmation")
    path = state_path(args.profile, state_dir_from(args))
    state = load_state(path)
    timestamp = now_iso()
    for topic in state["topics"]:
        topic["interview_count"] = 0
        topic["followup_count"] = 0
        topic["last_asked_at"] = None
        topic["last_result_at"] = None
        topic["mastery"] = None
        topic["hint_used"] = False
        topic["weakness"] = ""
        topic["focus_level"] = 0
        topic["focus_reason"] = ""
        topic["wrong_count"] = 0
        topic["review_count"] = 0
        topic["correct_streak"] = 0
        topic["last_reviewed_at"] = None
        topic["last_question_was_review"] = False
        topic["needs_correction"] = False
        topic["correction_count"] = 0
        topic["correction_reason"] = ""
        topic["correction_resolved_at"] = None
        topic["history"] = []
    state["updated_at"] = timestamp
    atomic_write(path, state)
    print(f"reset: {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--profile", required=True)
    init_parser.add_argument("--candidate", required=True)
    init_parser.add_argument("--role", required=True)
    init_parser.add_argument("--catalog", required=True)
    init_parser.set_defaults(func=command_init)

    asked_parser = subparsers.add_parser("mark-asked")
    asked_parser.add_argument("--profile", required=True)
    asked_parser.add_argument("--topic-id", required=True)
    asked_parser.add_argument("--mode", choices=("deep", "coverage"), required=True)
    asked_parser.add_argument("--question", required=True)
    asked_parser.set_defaults(func=command_mark_asked)

    followup_parser = subparsers.add_parser("mark-followup")
    followup_parser.add_argument("--profile", required=True)
    followup_parser.add_argument("--topic-id", required=True)
    followup_parser.add_argument("--question", required=True)
    followup_parser.set_defaults(func=command_mark_followup)

    result_parser = subparsers.add_parser("mark-result")
    result_parser.add_argument("--profile", required=True)
    result_parser.add_argument("--topic-id", required=True)
    result_parser.add_argument("--grade", choices=("A", "B", "C", "D"), required=True)
    result_parser.add_argument("--hint-used", action="store_true")
    result_parser.add_argument("--weakness", default="")
    result_parser.set_defaults(func=command_mark_result)

    focus_parser = subparsers.add_parser("mark-focus")
    focus_parser.add_argument("--profile", required=True)
    focus_parser.add_argument("--topic-id", required=True)
    focus_parser.add_argument("--level", type=int, choices=(1, 2, 3), required=True)
    focus_parser.add_argument("--reason", required=True)
    focus_parser.set_defaults(func=command_mark_focus)

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--profile", required=True)
    report_parser.add_argument("--json", action="store_true")
    report_parser.add_argument("--focus-only", action="store_true")
    report_parser.set_defaults(func=command_report)

    dashboard_parser = subparsers.add_parser("dashboard")
    dashboard_parser.add_argument("--profile", required=True)
    dashboard_parser.set_defaults(func=command_dashboard)

    reset_parser = subparsers.add_parser("reset")
    reset_parser.add_argument("--profile", required=True)
    reset_parser.add_argument("--yes", action="store_true")
    reset_parser.set_defaults(func=command_reset)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
