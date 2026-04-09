#!/usr/bin/env python3
"""Find code-related files inside a folder.

Usage:
    python scan_code_files.py C:\\path\\to\\folder
    python scan_code_files.py C:\\path\\to\\folder --json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

CODE_EXTENSIONS = {
    ".c",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".json",
    ".kt",
    ".m",
    ".mm",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sql",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
}

CODE_FILENAMES = {
    "Dockerfile",
    "Makefile",
    "CMakeLists.txt",
    "Gemfile",
    "Pipfile",
    "Procfile",
    "Vagrantfile",
    "biome.json",
    "build.gradle",
    "bun.lockb",
    "gradlew",
    "mvnw",
    "package.json",
    "package-lock.json",
    "pnpm-workspace.yaml",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "pyproject.toml",
    "Cargo.toml",
    "deno.json",
    "deno.jsonc",
    "go.mod",
    "go.sum",
    "composer.json",
    "composer.lock",
    "tsconfig.json",
    "vite.config.ts",
    "vite.config.js",
    "webpack.config.js",
    "eslint.config.js",
    ".eslintrc",
    ".eslintrc.json",
    ".prettierrc",
    ".gitignore",
}

SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "out",
    "target",
    "venv",
    ".venv",
    "__pycache__",
    ".idea",
    ".vscode",
}


def is_code_file(path: Path) -> bool:
    if not path.is_file():
        return False

    name = path.name
    if name in CODE_FILENAMES:
        return True

    if name.startswith(".") and path.suffix == "":
        return False

    return path.suffix.lower() in CODE_EXTENSIONS


def iter_code_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if is_code_file(path):
            yield path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search a folder for code-related files."
    )
    parser.add_argument("folder", help="Folder path to search")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print results as JSON instead of plain text",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.folder).expanduser().resolve()

    if not root.exists():
        raise SystemExit(f"Folder does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Not a folder: {root}")

    results = sorted(str(path.relative_to(root)) for path in iter_code_files(root))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for item in results:
            print(item)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
