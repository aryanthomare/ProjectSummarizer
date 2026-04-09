# 📚 Automated Codebase Auditing and Documentation Suite

## Project Overview

This suite provides a systematic, dual-component solution for managing the software development lifecycle. It automates the auditing process by first indexing an entire codebase and subsequently generating high-quality, holistic documentation and README files using locally hosted Large Language Models (LLMs).

## Features

*   **Recursive Codebase Indexing:** Utility to traverse and catalog all files within a target directory, generating a clean path inventory.
*   **LLM-Powered Documentation:** Integrates with local LLMs (via Ollama) to ingest raw file contents for analysis.
*   **Architecture Summarization:** Performs multi-stage analysis to create high-level summaries of the codebase architecture.
*   **Token Management:** Features structured prompting and token limit handling to ensure comprehensive documentation generation from large codebases.

## Tech Stack

*   **Primary Language:** Python
*   **Core Functionality:** Command Line Interface (CLI) Tooling
*   **AI Backend:** Large Language Models (LLMs) via Ollama
*   **Analysis:** Code Parsing, Natural Language Processing

## Project Structure

The suite is composed of two tightly coupled modules:

1.  **`file_scanner_utility`:** Responsible for the initial codebase ingestion. It recursively walks the provided path and creates a structured inventory file listing all accessible source code paths.
2.  **`documentation_generator`:** The CLI entry point. It consumes the inventory from the scanner, reads file contents, and orchestrates the structured prompting and API calls to the local LLM to synthesize documentation.

## Setup

1.  **Prerequisites:** Ensure Python 3.9+ is installed.
2.  **Ollama:** You must have [Ollama](https://ollama.com/) running locally. Pull the desired model (e.g., `ollama pull llama3`).
3.  **Installation:** Clone the repository and install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configuration:** Verify the `config.yaml` file points to your local Ollama endpoint.

## Usage

The process is executed in two distinct, sequential steps:

### 1. Scan the Codebase (Indexing)
Execute the scanner utility against your target project directory. This creates the required input inventory file.

```bash
python src/scanner/run_scan.py --path /path/to/your/codebase --output-inventory inventory.json
```

### 2. Generate Documentation (LLM Analysis)
Feed the generated inventory file to the documentation generator. This initiates the multi-stage LLM analysis.

```bash
python src/generator/generate_docs.py --inventory inventory.json --output-dir ./docs_output
```

The system will output structured summaries and a comprehensive `README.md` in the specified output directory.

## Notes

*   **LLM Dependency:** The success and quality of the output are directly dependent on the model available in Ollama.
*   **Scope Limitation:** For extremely large codebases (millions of lines), consider breaking the scanning process into manageable sub-directories to optimize token usage and processing time.
*   **Error Handling:** The system includes basic retry logic for network/API failures with Ollama.
