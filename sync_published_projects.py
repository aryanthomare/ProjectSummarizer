#!/usr/bin/env python3
"""Ensure Published projects have JSON/output.json and sync into website work-data.json.

Default behavior:
- Scans each direct child folder under Published.
- If <project>/JSON/output.json exists, generation is skipped.
- If missing, runs summarize_codebase.py to generate it.
- Loads each project's output JSON and upserts entries into the "Projects" section
  of work-data.json by title.

Usage:
    python sync_published_projects.py
    python sync_published_projects.py --published-root "C:/path/to/Published"
    python sync_published_projects.py --work-data "C:/path/to/work-data.json"
    python sync_published_projects.py --project "SomeProject" --force-regenerate --no-git-sync
    python sync_published_projects.py --check-work-data
    python sync_published_projects.py --show-work-data-json
    python sync_published_projects.py --commit-message "Update work-data.json"
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


DEFAULT_PUBLISHED_ROOT = Path(r"C:\Users\Aryan\OneDrive\Documents\Development\Published")
DEFAULT_WORK_DATA = Path(
    r"C:\Users\Aryan\OneDrive\Documents\Development\PersonalWebsite\aryanthomare.github.io\work-data.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate missing project output.json files and sync them into work-data.json"
    )
    parser.add_argument(
        "--published-root",
        default=str(DEFAULT_PUBLISHED_ROOT),
        help="Root folder containing project directories",
    )
    parser.add_argument(
        "--work-data",
        default=str(DEFAULT_WORK_DATA),
        help="Path to website work-data.json file",
    )
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        help=(
            "Project folder name under published root, or an absolute project path. "
            "Can be passed multiple times."
        ),
    )
    parser.add_argument(
        "--force-regenerate",
        action="store_true",
        help="Regenerate JSON/output.json even when it already exists",
    )
    parser.add_argument(
        "--commit-message",
        default="Update work-data.json",
        help="Git commit message used when syncing website repo",
    )
    parser.add_argument(
        "--git-remote",
        default="origin",
        help="Git remote name to push to",
    )
    parser.add_argument(
        "--git-branch",
        default="",
        help="Git branch to push (default: current branch)",
    )
    parser.add_argument(
        "--git-sync",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Run git add/commit/push for work-data.json after sync (default: disabled)",
    )
    parser.add_argument(
        "--check-work-data",
        action="store_true",
        help="Report whether work-data.json would change without writing it",
    )
    parser.add_argument(
        "--show-work-data-json",
        action="store_true",
        help="Print the project-entry JSON that would be merged into work-data.json",
    )
    return parser.parse_args()


def run_summarizer(project_dir: Path, summarize_script: Path) -> None:
    command = [
        sys.executable,
        str(summarize_script),
        str(project_dir),
        "--model",
        "gemma4",
        "--generate-readme",
        "--json",
        "--max-file-tokens",
        "2000",
        "--max-context-tokens",
        "500000",
        "--show-batch-responses",
    ]
    print(f"[sync] Generating output for: {project_dir}")
    subprocess.run(command, check=True)


def ensure_output_json(project_dir: Path, summarize_script: Path, force_regenerate: bool) -> Path:
    output_path = project_dir / "JSON" / "output.json"
    if output_path.exists() and not force_regenerate:
        print(f"[sync] Exists, skipping generation: {output_path}")
        return output_path

    run_summarizer(project_dir, summarize_script)

    if not output_path.exists():
        raise RuntimeError(f"Expected output JSON was not created: {output_path}")

    return output_path


def resolve_project_dirs(published_root: Path, project_filters: list[str]) -> list[Path]:
    if not project_filters:
        return sorted(path for path in published_root.iterdir() if path.is_dir())

    selected: list[Path] = []
    seen: set[Path] = set()

    for raw in project_filters:
        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidate = published_root / candidate
        candidate = candidate.resolve()

        if not candidate.exists() or not candidate.is_dir():
            raise SystemExit(f"Invalid project directory: {raw}")

        if candidate not in seen:
            selected.append(candidate)
            seen.add(candidate)

    return selected


def load_project_summary(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected object JSON in {path}")

    title = data.get("title", "N/A")
    date = data.get("date", "N/A")
    description = data.get("description", "N/A")
    tags = data.get("tags", [])
    link = data.get("link", "N/A")

    if not isinstance(tags, list):
        tags = []

    return {
        "title": title,
        "date": date,
        "description": description,
        "tags": tags,
        "link": link,
    }


def get_projects_items(work_data: dict[str, Any]) -> list[dict[str, Any]]:
    sections = work_data.get("sections")
    if not isinstance(sections, list):
        raise ValueError("work-data.json is missing a valid 'sections' array")

    for section in sections:
        if isinstance(section, dict) and section.get("title") == "Projects":
            items = section.get("items")
            if isinstance(items, list):
                return items
            section["items"] = []
            return section["items"]

    projects_section = {"title": "Projects", "items": []}
    sections.append(projects_section)
    return projects_section["items"]


def upsert_projects(items: list[dict[str, Any]], new_entries: list[dict[str, Any]]) -> None:
    index_by_title: dict[str, int] = {}
    for index, item in enumerate(items):
        title = item.get("title")
        if isinstance(title, str):
            index_by_title[title.strip().lower()] = index

    to_prepend: list[dict[str, Any]] = []

    for entry in new_entries:
        title = str(entry.get("title", "")).strip()
        key = title.lower()
        if key and key in index_by_title:
            items[index_by_title[key]] = entry
        else:
            to_prepend.append(entry)

    if to_prepend:
        items[0:0] = to_prepend


def git_output(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=str(cwd), check=True, capture_output=True, text=True)


def git_sync_work_data(
    work_data_path: Path,
    commit_message: str,
    remote: str,
    branch: str,
) -> None:
    repo_dir = work_data_path.parent

    try:
        top_level_result = git_output(["git", "rev-parse", "--show-toplevel"], repo_dir)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Failed to detect git repository for {work_data_path}: {exc}") from exc

    repo_root = Path(top_level_result.stdout.strip()).resolve()
    relative_work_data = work_data_path.resolve().relative_to(repo_root)

    git_output(["git", "add", str(relative_work_data)], repo_root)

    staged_check = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", str(relative_work_data)],
        cwd=str(repo_root),
        check=False,
    )
    if staged_check.returncode == 0:
        print(f"[sync] No git changes to commit for {relative_work_data}")
        return
    if staged_check.returncode != 1:
        raise RuntimeError("Failed to check staged git changes")

    git_output(["git", "commit", "-m", commit_message], repo_root)

    target_branch = branch.strip()
    if not target_branch:
        branch_result = git_output(["git", "branch", "--show-current"], repo_root)
        target_branch = branch_result.stdout.strip()
        if not target_branch:
            raise RuntimeError("Could not determine current git branch")

    git_output(["git", "push", remote, target_branch], repo_root)
    print(f"[sync] Pushed {relative_work_data} to {remote}/{target_branch}")


def main() -> int:
    args = parse_args()

    published_root = Path(args.published_root).expanduser().resolve()
    work_data_path = Path(args.work_data).expanduser().resolve()
    summarize_script = Path(__file__).with_name("summarize_codebase.py").resolve()

    if not published_root.exists() or not published_root.is_dir():
        raise SystemExit(f"Published root is invalid: {published_root}")
    if not summarize_script.exists():
        raise SystemExit(f"Missing summarize script: {summarize_script}")
    if not work_data_path.exists():
        raise SystemExit(f"Missing work-data file: {work_data_path}")

    project_dirs = resolve_project_dirs(published_root, args.project)
    print(f"[sync] Using {len(project_dirs)} project folder(s)")

    new_entries: list[dict[str, Any]] = []

    for project_dir in project_dirs:
        try:
            output_path = ensure_output_json(project_dir, summarize_script, args.force_regenerate)
            summary = load_project_summary(output_path)
            new_entries.append(summary)
        except Exception as exc:  # noqa: BLE001
            print(f"[sync] Skipped {project_dir.name}: {exc}")

    original_work_data_text = work_data_path.read_text(encoding="utf-8")
    work_data = json.loads(original_work_data_text)
    if not isinstance(work_data, dict):
        raise SystemExit("work-data.json root must be an object")

    items = get_projects_items(work_data)
    upsert_projects(items, new_entries)

    if args.show_work_data_json:
        print(json.dumps(new_entries, indent=2))

    updated_work_data_text = json.dumps(work_data, indent=2) + "\n"
    work_data_changed = updated_work_data_text != original_work_data_text

    if args.check_work_data:
        status = "would change" if work_data_changed else "would not change"
        print(f"[sync] {work_data_path} {status}")
    elif work_data_changed:
        work_data_path.write_text(updated_work_data_text, encoding="utf-8")
        print(f"[sync] Updated {work_data_path} with {len(new_entries)} project summary item(s)")
    else:
        print(f"[sync] No changes needed for {work_data_path}")

    if args.git_sync and work_data_changed and not args.check_work_data:
        git_sync_work_data(
            work_data_path=work_data_path,
            commit_message=args.commit_message,
            remote=args.git_remote,
            branch=args.git_branch,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
