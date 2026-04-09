# Project Summarizer

Find code-related files in a folder tree.

## Usage

```bash
python scan_code_files.py C:\path\to\folder
python scan_code_files.py C:\path\to\folder --json

python summarize_codebase.py C:\path\to\folder
python summarize_codebase.py C:\path\to\folder --model gemma4
python summarize_codebase.py C:\path\to\folder --max-context-tokens 8000
python summarize_codebase.py C:\path\to\folder --system-prompt-file system_prompt.md --prompt-file prompt.md
python summarize_codebase.py C:\path\to\folder --batch-prompt-file batch_prompt.md
python summarize_codebase.py C:\path\to\folder --verbose
python summarize_codebase.py C:\path\to\folder --generate-readme --output-readme README.generated.md
```

The script walks the folder recursively, skips common build and dependency directories, and prints matching file paths relative to the folder you passed in.

The summarizer script reads the code files, groups them into context batches, and sends them to a local Ollama server at `http://localhost:11434` by default.

It loads the system prompt and user prompt from markdown files.
- `system_prompt.md`
- `prompt.md`
- `batch_prompt.md`
- `readme_prompt.md`

If either file is missing or empty, the script uses built-in defaults.

Use `--verbose` to print runtime progress logs (scan path, files being read, batch progress, and Ollama request phases) while also requesting a more detailed summary from the model.

Use `--generate-readme` to produce a README file from the final summary. After writing the README, the script reads only that README back in and sends it through `prompt.md` to produce the JSON summary output. Use `--output-readme` to choose where the README is written. Relative paths are resolved under the target repository folder.
