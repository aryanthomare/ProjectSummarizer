# Project Summarizer

Project Summarizer helps you generate structured project summaries for repositories in your Published folder, then sync those summaries into your website data file.

## What It Does

1. Scans repositories for code-related files.
2. Summarizes codebases with a local Ollama model.
3. Produces machine-friendly JSON output in each project.
4. Optionally generates README-style markdown summaries.
5. Syncs all (or selected) project summaries into website `work-data.json`.
6. Optionally commits and pushes website changes to GitHub.

## Scripts

### `scan_code_files.py`

Recursively lists code-related files for a target folder.

```bash
python scan_code_files.py C:\path\to\folder
python scan_code_files.py C:\path\to\folder --json
```

#### CLI Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `folder` | positional | *(required)* | Folder path to search for code files |
| `--json` | flag | `false` | Print results as a JSON array instead of plain text, one path per line |

### `summarize_codebase.py`

Reads code files and sends batched context to Ollama (default URL: `http://localhost:11434`, default model: `gemma4`).
Python files are always included in full; the per-file token cap only applies to non-Python files.

Common usage:

```bash
python summarize_codebase.py C:\path\to\repo
python summarize_codebase.py C:\path\to\repo --model gemma4
python summarize_codebase.py C:\path\to\repo --max-context-tokens 8000
python summarize_codebase.py C:\path\to\repo --max-file-tokens 100
python summarize_codebase.py C:\path\to\repo --verbose --show-batch-responses
python summarize_codebase.py C:\path\to\repo --generate-readme --output-readme JSON\readme.generated.md
python summarize_codebase.py C:\path\to\repo --json --output-json JSON\output.json
```

#### CLI Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `folder` | positional | *(required)* | Folder path of the repository to summarize |
| `--model` | string | `gemma4` | Ollama model name to use for summarization |
| `--ollama-url` | string | `http://localhost:11434` | Base URL of the Ollama API |
| `--max-context-tokens` | int | `8000` | Maximum estimated tokens per batch before sending to the model |
| `--max-file-tokens` | int | `2000` | Maximum estimated tokens to keep from any single non-Python file; `0` keeps the full file |
| `--system-prompt-file` | path | `system_prompt.md` | Markdown file containing the system prompt |
| `--prompt-file` | path | `prompt.md` | Markdown file containing the user prompt |
| `--batch-prompt-file` | path | `batch_prompt.md` | Markdown file containing the per-batch prompt |
| `--readme-prompt-file` | path | `readme_prompt.md` | Markdown file containing the README generation prompt |
| `--generate-readme` | flag | `false` | Generate a README markdown file from the repository summary |
| `--output-readme` | path | `JSON/readme.generated.md` | Output path for the generated README (relative paths resolved under the target folder) |
| `--verbose` | flag | `false` | Enable detailed runtime logs and request a more detailed summary from Ollama |
| `--show-batch-responses` | flag | `false` | Print each batch response from the LLM to stderr |
| `--json` | flag | `false` | Print the final summary response as JSON |
| `--output-json` | path | `JSON/output.json` | Write JSON output to this path (relative paths resolved under the target folder) |

Prompt files used by default:

1. `system_prompt.md`
2. `prompt.md`
3. `batch_prompt.md`
4. `readme_prompt.md`

If a prompt file is missing or empty, built-in defaults are used.

### `sync_published_projects.py`

Syncs project summaries into your website data file.

Behavior:

1. Finds project folders under Published (or only those passed with `--project`).
2. Ensures `JSON/output.json` exists per project.
3. Regenerates missing outputs (or all selected outputs with `--force-regenerate`).
4. Upserts entries into the `Projects` section of `work-data.json` by title.
5. Git sync is optional and disabled by default.

#### CLI Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--published-root` | path | `C:\Users\Aryan\...\Published` | Root folder containing project directories |
| `--work-data` | path | `C:\Users\Aryan\...\work-data.json` | Path to the website `work-data.json` file |
| `--project` | string *(repeatable)* | *(all projects)* | Project folder name under Published root, or an absolute project path. Pass multiple times to select several projects |
| `--force-regenerate` | flag | `false` | Regenerate `JSON/output.json` even when it already exists |
| `--check-work-data` | flag | `false` | Report whether `work-data.json` would change without actually writing it |
| `--show-work-data-json` | flag | `false` | Print the project-entry JSON that would be merged into `work-data.json` |
| `--git-sync` / `--no-git-sync` | flag | `false` | Run `git add`/`commit`/`push` for `work-data.json` after syncing |
| `--commit-message` | string | `"Update work-data.json"` | Git commit message used when `--git-sync` is enabled |
| `--git-remote` | string | `origin` | Git remote name to push to |
| `--git-branch` | string | *(current branch)* | Git branch to push; defaults to the current branch when omitted |

## Key Defaults

1. Published root defaults to:
	`C:\Users\Aryan\OneDrive\Documents\Development\Published`
2. Website data file defaults to:
	`C:\Users\Aryan\OneDrive\Documents\Development\PersonalWebsite\aryanthomare.github.io\work-data.json`
3. Git sync default is disabled (`--no-git-sync` behavior).

## Workflows

### 1) Sync everything without Git (default)

```bash
python sync_published_projects.py
```

### 2) Regenerate one specific project only, no Git

```bash
python sync_published_projects.py --project "ProjectSummarizer" --force-regenerate --no-git-sync
```

You can also pass an absolute path:

```bash
python sync_published_projects.py --project "C:\Users\Aryan\OneDrive\Documents\Development\Published\ProjectSummarizer" --force-regenerate --no-git-sync
```

### 3) Regenerate multiple specific projects

```bash
python sync_published_projects.py --project "ProjectA" --project "ProjectB" --force-regenerate
```

### 4) Sync and also commit/push website data

```bash
python sync_published_projects.py --git-sync --commit-message "Sync published project summaries"
```

### 5) Check whether work-data would change

```bash
python sync_published_projects.py --check-work-data
```

### 6) Print the JSON that would be merged into work-data

```bash
python sync_published_projects.py --show-work-data-json
```

Optional Git controls:

```bash
python sync_published_projects.py --git-sync --git-remote origin --git-branch master
```

## Notes

1. `--project` accepts either folder names under Published or absolute paths.
2. Project matching in website data is title-based and case-insensitive.
3. New project entries are prepended in the `Projects` list.
4. Git operations only stage/commit/push the website `work-data.json` file.
