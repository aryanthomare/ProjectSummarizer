# Codebase Documentation Pipeline

## Project Overview
The Codebase Documentation Pipeline is an automated, multi-stage CI/CD system engineered to generate comprehensive, structured documentation and detailed project metadata from multiple disparate code repositories. It provides a unified inventory of codebase contents, abstracting complex analysis into a single, manageable manifest.

## Features
*   **Automated Scanning:** Orchestrates the scanning of multiple connected code projects via `sync_published_projects.py`.
*   **Intelligent Metadata Augmentation:** If initial metadata collection is incomplete, the system triggers LLM-powered analysis.
*   **Deep Code Analysis:** Utilizes `scan_code_files.py` for recursive file gathering, feeding content into specialized summarization scripts.
*   **LLM Integration:** Leverages Ollama for on-premises, scalable code summarization and feature extraction, managed by `summarize_codebase.py`.
*   **Centralized Manifest:** Aggregates all outputs into a single `work-data.json` file for a complete, queryable project inventory.

## Tech Stack
*   **Core Language:** Python
*   **Deployment:** CI/CD Pipeline Architecture
*   **AI/NLP:** Ollama (for local LLM integration)
*   **Functionality:** Data Pipeline Orchestration, Metadata Management

## Project Structure
The pipeline is organized around several key Python modules that manage the workflow stages:

```
/
├── sync_published_projects.py  # Orchestrates initial project discovery and coordination.
├── scan_code_files.py          # Handles recursive file traversal and content extraction.
├── summarize_codebase.py       # Manages the LLM interaction and generates summary narratives.
├── requirements.txt            # Lists all necessary Python dependencies.
└── README.md
```

## Setup
1.  **Clone the Repository:**
    ```bash
    git clone <repository-url>
    cd ProjectSummarizer
    ```
2.  **Install Dependencies:** Ensure you have Python 3.8+ installed.
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure Ollama:** Ensure the Ollama service is running locally and that the necessary models (e.g., `llama2`) are pulled before running the pipeline.

## Usage
To execute a full documentation generation cycle, run the main orchestration script:

```bash
python sync_published_projects.py
```

**Workflow Execution:**
1.  `sync_published_projects.py` identifies all target repositories.
2.  It calls `scan_code_files.py` to gather raw content.
3.  If data gaps are detected, it calls `summarize_codebase.py`, which interfaces with Ollama to generate detailed summaries for the missing sections.
4.  The final results are compiled and saved to `work-data.json`.

## Notes
*   The pipeline assumes network connectivity for discovering initial projects, but the core analysis relies on local Ollama instances.
*   The output file, `work-data.json`, is the source of truth for all derived project metadata and should be archived after successful runs.
*   For debugging, run modules individually (e.g., `python scan_code_files.py --target <directory>`) to isolate bottlenecks.
