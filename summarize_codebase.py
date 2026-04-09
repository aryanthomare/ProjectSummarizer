#!/usr/bin/env python3
"""Summarize a codebase with a local Ollama model.

Usage:
    python summarize_codebase.py C:\\path\\to\\folder
    python summarize_codebase.py C:\\path\\to\\folder --model gemma4
    python summarize_codebase.py C:\\path\\to\\folder --max-context-tokens 8000
    python summarize_codebase.py C:\\path\\to\\folder --system-prompt-file system_prompt.md --prompt-file prompt.md --batch-prompt-file batch_prompt.md
    python summarize_codebase.py C:\\path\\to\\folder --verbose
    python summarize_codebase.py C:\\path\\to\\folder --generate-readme --output-readme README.generated.md
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib import error, request

from scan_code_files import iter_code_files

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "gemma4"
DEFAULT_MAX_CONTEXT_TOKENS = 8000
DEFAULT_MAX_FILE_TOKENS = 2000
CHARS_PER_TOKEN = 4
DEFAULT_SYSTEM_PROMPT = (
    "You are a senior software engineer summarizing codebases. "
    "If the input is incomplete because of truncation, mention that briefly."
)
DEFAULT_USER_PROMPT = (
    "Summarize the provided code context for another developer. "
    "Focus on purpose, architecture, main modules, important flows, and notable risks."
)
DEFAULT_BATCH_PROMPT = (
    "Summarize this subset of repository files. "
    "Focus on what these files do and how they connect to the rest of the project."
)
DEFAULT_README_PROMPT = (
    "Create a high-quality README.md for this repository using the provided summary. "
    "Return only markdown and include sections: Project Overview, Features, Tech Stack, "
    "Project Structure, Setup, Usage, and Notes."
)


@dataclass(frozen=True)
class FileBatch:
    files: list[Path]
    combined_text: str


def parse_args() -> argparse.Namespace:
    default_system_prompt_file = Path(__file__).with_name("system_prompt.md")
    default_prompt_file = Path(__file__).with_name("prompt.md")
    default_batch_prompt_file = Path(__file__).with_name("batch_prompt.md")
    default_readme_prompt_file = Path(__file__).with_name("readme_prompt.md")

    parser = argparse.ArgumentParser(
        description="Summarize code files in a folder using an Ollama model."
    )
    parser.add_argument("folder", help="Folder path to summarize")
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Ollama model name to use (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--ollama-url",
        default=DEFAULT_OLLAMA_URL,
        help=f"Base URL for Ollama (default: {DEFAULT_OLLAMA_URL})",
    )
    parser.add_argument(
        "--max-context-tokens",
        type=int,
        default=DEFAULT_MAX_CONTEXT_TOKENS,
        help="Maximum estimated tokens per context batch before sending to the model",
    )
    parser.add_argument(
        "--max-file-tokens",
        type=int,
        default=DEFAULT_MAX_FILE_TOKENS,
        help="Maximum estimated tokens to keep from any single file",
    )
    parser.add_argument(
        "--system-prompt-file",
        default=str(default_system_prompt_file),
        help="Markdown file containing the system prompt",
    )
    parser.add_argument(
        "--prompt-file",
        default=str(default_prompt_file),
        help="Markdown file containing the user prompt",
    )
    parser.add_argument(
        "--batch-prompt-file",
        default=str(default_batch_prompt_file),
        help="Markdown file containing the batch-level prompt",
    )
    parser.add_argument(
        "--readme-prompt-file",
        default=str(default_readme_prompt_file),
        help="Markdown file containing the README generation prompt",
    )
    parser.add_argument(
        "--generate-readme",
        action="store_true",
        help="Generate a README markdown file from the repository summary",
    )
    parser.add_argument(
        "--output-readme",
        default="README.generated.md",
        help="Output README path when --generate-readme is used (relative paths are resolved under the target folder)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed runtime logs and ask Ollama for a more detailed summary",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the final response as JSON",
    )
    return parser.parse_args()


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN)


def log_verbose(enabled: bool, message: str) -> None:
    if enabled:
        print(f"[verbose] {message}", file=sys.stderr, flush=True)


def load_markdown_prompt(path_text: str, fallback: str, label: str, verbose: bool) -> str:
    path = Path(path_text).expanduser().resolve()

    if not path.exists():
        log_verbose(verbose, f"{label}: file not found at {path}; using built-in fallback")
        return fallback

    if not path.is_file():
        raise SystemExit(f"{label} is not a file: {path}")

    try:
        content = path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError as exc:
        raise SystemExit(f"Failed to read {label} from {path}: {exc}") from exc

    if not content:
        log_verbose(verbose, f"{label}: file is empty at {path}; using built-in fallback")
        return fallback

    log_verbose(verbose, f"{label}: loaded from {path}")
    return content


def fetch_ollama_models(ollama_url: str, verbose: bool) -> list[str]:
    url = ollama_url.rstrip("/") + "/api/tags"
    req = request.Request(url, method="GET")
    log_verbose(verbose, f"Requesting installed models from {url}")

    try:
        with request.urlopen(req) as response:
            body = response.read().decode("utf-8")
    except error.URLError as exc:
        raise SystemExit(
            f"Failed to query Ollama model list at {ollama_url}: {exc}. Make sure Ollama is running."
        ) from exc

    payload = json.loads(body)
    models = payload.get("models", [])
    result = [str(item.get("name", "")) for item in models if item.get("name")]
    log_verbose(verbose, f"Found {len(result)} installed models")
    return result


def resolve_model_name(ollama_url: str, requested_model: str, verbose: bool) -> str:
    available_models = fetch_ollama_models(ollama_url, verbose)
    if requested_model in available_models:
        log_verbose(verbose, f"Using exact model name: {requested_model}")
        return requested_model

    alias_matches = [name for name in available_models if name.startswith(requested_model + ":")]
    if len(alias_matches) == 1:
        log_verbose(verbose, f"Resolved model alias {requested_model!r} -> {alias_matches[0]!r}")
        return alias_matches[0]

    if alias_matches:
        log_verbose(verbose, f"Multiple alias matches for {requested_model!r}; using {alias_matches[0]!r}")
        return alias_matches[0]

    log_verbose(verbose, f"No alias match found for {requested_model!r}; using it as provided")
    return requested_model


def read_file_text(path: Path, max_tokens: int) -> str:
    max_chars = max_tokens * CHARS_PER_TOKEN
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "[unreadable file]"

    if len(text) <= max_chars:
        return text

    return text[:max_chars] + "\n\n[truncated]\n"


def build_file_prompt(root: Path, files: Iterable[Path], max_file_tokens: int, verbose: bool) -> str:
    parts: list[str] = []
    for path in files:
        relative_path = path.relative_to(root)
        log_verbose(verbose, f"Reading file: {relative_path}")
        content = read_file_text(path, max_file_tokens)
        parts.append(
            f"### File: {relative_path}\n"
            f"```{path.suffix.lstrip('.') if path.suffix else 'text'}\n"
            f"{content}\n"
            f"```"
        )
    return "\n\n".join(parts)


def split_into_batches(
    root: Path,
    files: list[Path],
    max_context_tokens: int,
    max_file_tokens: int,
    verbose: bool,
) -> list[FileBatch]:
    batches: list[FileBatch] = []
    current_files: list[Path] = []
    current_parts: list[str] = []
    current_tokens = 0

    for path in files:
        file_block = build_file_prompt(root, [path], max_file_tokens, verbose)
        file_tokens = estimate_tokens(file_block)

        if current_files and current_tokens + file_tokens > max_context_tokens:
            log_verbose(
                verbose,
                f"Closing batch {len(batches) + 1}: {len(current_files)} files, ~{current_tokens} tokens",
            )
            batches.append(
                FileBatch(
                    files=current_files.copy(),
                    combined_text="\n\n".join(current_parts),
                )
            )
            current_files.clear()
            current_parts.clear()
            current_tokens = 0

        current_files.append(path)
        current_parts.append(file_block)
        current_tokens += file_tokens

    if current_files:
        log_verbose(
            verbose,
            f"Closing batch {len(batches) + 1}: {len(current_files)} files, ~{current_tokens} tokens",
        )
        batches.append(
            FileBatch(
                files=current_files.copy(),
                combined_text="\n\n".join(current_parts),
            )
        )

    log_verbose(verbose, f"Prepared {len(batches)} batch(es)")
    return batches


def ollama_generate(
    ollama_url: str,
    model: str,
    prompt: str,
    system: str | None = None,
    *,
    verbose: bool,
    phase: str,
) -> str:
    payload: dict[str, object] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    data = json.dumps(payload).encode("utf-8")
    url = ollama_url.rstrip("/") + "/api/generate"
    log_verbose(verbose, f"Sending {phase} request to {url} using model {model!r} (~{estimate_tokens(prompt)} prompt tokens)")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        if exc.code == 404:
            raise SystemExit(
                f"Ollama returned 404 for model {model!r}. The model is probably not installed under that exact name. "
                f"Try --model with one of the names from /api/tags, such as gemma4:26b."
            ) from exc
        raise SystemExit(
            f"Ollama request failed with HTTP {exc.code} for model {model!r}: {exc.reason}"
        ) from exc
    except error.URLError as exc:
        raise SystemExit(
            f"Failed to connect to Ollama at {ollama_url}: {exc}. Make sure Ollama is running."
        ) from exc

    result = json.loads(body)
    text = str(result.get("response", "")).strip()
    log_verbose(verbose, f"Completed {phase} request ({len(text)} chars in response)")
    return text


def verbose_prompt_suffix(verbose: bool) -> str:
    if not verbose:
        return ""
    return (
        "\n\nVerbosity mode: enabled. "
        "Provide a detailed explanation with concrete file-level insights, notable implementation details, "
        "and clear technical reasoning."
    )


def sanitize_markdown_output(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```markdown") and cleaned.endswith("```"):
        return cleaned[len("```markdown"): -3].strip()
    if cleaned.startswith("```md") and cleaned.endswith("```"):
        return cleaned[len("```md"): -3].strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        return cleaned[3:-3].strip()
    return cleaned


def resolve_output_path(root: Path, output_path_text: str) -> Path:
    path = Path(output_path_text).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def generate_readme_markdown(
    ollama_url: str,
    model: str,
    root: Path,
    summary_text: str,
    system_prompt: str,
    readme_prompt: str,
    verbose: bool,
) -> str:
    prompt = (
        f"{readme_prompt}{verbose_prompt_suffix(verbose)}\n\n"
        f"Repository root: {root}\n\n"
        "Repository summary:\n"
        f"{summary_text}\n\n"
        "Output requirements:\n"
        "- Return only markdown\n"
        "- Use clear section headers\n"
        "- Keep setup and usage concrete\n"
    )
    response = ollama_generate(
        ollama_url,
        model,
        prompt,
        system=system_prompt,
        verbose=verbose,
        phase="readme generation",
    )
    return sanitize_markdown_output(response)


def summarize_readme_json(
    ollama_url: str,
    model: str,
    readme_path: Path,
    system_prompt: str,
    json_prompt: str,
    verbose: bool,
) -> str:
    log_verbose(verbose, f"Reading README content from {readme_path} for JSON summarization")
    try:
        readme_text = readme_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise SystemExit(f"Failed to read generated README from {readme_path}: {exc}") from exc

    prompt = (
        f"{json_prompt}{verbose_prompt_suffix(verbose)}\n\n"
        "Task: Summarize the following README content into the requested JSON format. "
        "Return only valid JSON and do not include markdown fences.\n\n"
        f"README path: {readme_path}\n\n"
        f"{readme_text}"
    )
    return ollama_generate(
        ollama_url,
        model,
        prompt,
        system=system_prompt,
        verbose=verbose,
        phase="README JSON summary",
    )


def summarize_batch(
    ollama_url: str,
    model: str,
    batch: FileBatch,
    root: Path,
    system_prompt: str,
    batch_prompt: str,
    verbose: bool,
    batch_index: int,
    batch_total: int,
) -> str:
    log_verbose(verbose, f"Starting batch {batch_index}/{batch_total} with {len(batch.files)} file(s)")
    prompt = (
        f"{batch_prompt}{verbose_prompt_suffix(verbose)}\n\n"
        "Task: Summarize this batch of repository files.\n\n"
        f"Repository root: {root}\n"
        f"Files in this batch: {len(batch.files)}\n\n"
        f"{batch.combined_text}"
    )
    return ollama_generate(
        ollama_url,
        model,
        prompt,
        system=system_prompt,
        verbose=verbose,
        phase=f"batch {batch_index}/{batch_total}",
    )


def summarize_overall(
    ollama_url: str,
    model: str,
    root: Path,
    batch_summaries: list[str],
    system_prompt: str,
    user_prompt: str,
    verbose: bool,
) -> str:
    log_verbose(verbose, f"Starting final summary synthesis from {len(batch_summaries)} batch summary item(s)")
    prompt = (
        f"{user_prompt}{verbose_prompt_suffix(verbose)}\n\n"
        "Task: Combine these batch summaries into one repository summary. "
        "Include the overall purpose, main components, key dependencies or frameworks, and any notable risks or next steps.\n\n"
        + "\n\n".join(
            f"### Batch {index + 1}\n{summary}"
            for index, summary in enumerate(batch_summaries)
        )
    )
    return ollama_generate(
        ollama_url,
        model,
        prompt,
        system=system_prompt,
        verbose=verbose,
        phase="final summary",
    )


def main() -> int:
    args = parse_args()
    root = Path(args.folder).expanduser().resolve()
    log_verbose(args.verbose, f"Starting summarization run in {root}")

    if not root.exists():
        raise SystemExit(f"Folder does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Not a folder: {root}")
    if args.max_context_tokens <= 0:
        raise SystemExit("--max-context-tokens must be greater than zero")
    if args.max_file_tokens <= 0:
        raise SystemExit("--max-file-tokens must be greater than zero")

    log_verbose(args.verbose, f"Scanning code files under {root}")
    files = sorted(iter_code_files(root))
    log_verbose(args.verbose, f"Found {len(files)} code-related file(s)")
    if not files:
        raise SystemExit("No code-related files were found in that folder.")

    system_prompt = load_markdown_prompt(
        args.system_prompt_file,
        fallback=DEFAULT_SYSTEM_PROMPT,
        label="System prompt file",
        verbose=args.verbose,
    )
    user_prompt = load_markdown_prompt(
        args.prompt_file,
        fallback=DEFAULT_USER_PROMPT,
        label="Prompt file",
        verbose=args.verbose,
    )
    batch_prompt = load_markdown_prompt(
        args.batch_prompt_file,
        fallback=DEFAULT_BATCH_PROMPT,
        label="Batch prompt file",
        verbose=args.verbose,
    )
    readme_prompt = load_markdown_prompt(
        args.readme_prompt_file,
        fallback=DEFAULT_README_PROMPT,
        label="README prompt file",
        verbose=args.verbose,
    )

    model = resolve_model_name(args.ollama_url, args.model, args.verbose)
    batches = split_into_batches(
        root,
        files,
        args.max_context_tokens,
        args.max_file_tokens,
        args.verbose,
    )
    batch_summaries = [
        summarize_batch(
            args.ollama_url,
            model,
            batch,
            root,
            system_prompt,
            batch_prompt,
            args.verbose,
            batch_index=index + 1,
            batch_total=len(batches),
        )
        for index, batch in enumerate(batches)
    ]
    final_summary = summarize_overall(
        args.ollama_url,
        model,
        root,
        batch_summaries,
        system_prompt,
        user_prompt,
        args.verbose,
    )

    readme_output_path: Path | None = None
    if args.generate_readme:
        log_verbose(args.verbose, "Generating README markdown from final summary")
        readme_markdown = generate_readme_markdown(
            args.ollama_url,
            model,
            root,
            final_summary,
            system_prompt,
            readme_prompt,
            args.verbose,
        )
        readme_output_path = resolve_output_path(root, args.output_readme)
        readme_output_path.parent.mkdir(parents=True, exist_ok=True)
        readme_output_path.write_text(readme_markdown + "\n", encoding="utf-8")
        log_verbose(args.verbose, f"Wrote generated README to {readme_output_path}")

        readme_json = summarize_readme_json(
            args.ollama_url,
            model,
            readme_output_path,
            system_prompt,
            user_prompt,
            args.verbose,
        )

        print(readme_json)
        return 0

    if args.json:
        print(
            json.dumps(
                {
                    "root": str(root),
                    "model": model,
                    "batch_count": len(batches),
                    "verbose": args.verbose,
                    "readme_generated": args.generate_readme,
                    "readme_output_path": str(readme_output_path) if readme_output_path else None,
                    "summary": final_summary,
                },
                indent=2,
            )
        )
    else:
        print(final_summary)
        if readme_output_path:
            print(f"\nGenerated README: {readme_output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
