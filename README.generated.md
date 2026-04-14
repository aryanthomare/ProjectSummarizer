# 🧠 Codebase Intelligence Toolkit (Scanner & Doc Generator)

## 📚 Project Overview

This toolkit provides a cohesive Command Line Interface (CLI) utility suite designed for deep, automated comprehension and documentation of source codebases. By integrating structural scanning with local Large Language Models (LLMs) via Ollama, the system generates high-quality, structured technical documentation, most notably comprehensive `README.md` files, enabling seamless integration into static analysis pipelines.

## ✨ Features

*   **Codebase Scanning:** Automatically discovers and maps the file structure of any provided directory.
*   **LLM Orchestration:** Manages interaction with local LLMs via Ollama, including intelligent token chunking to handle large source files contextually.
*   **Structured Documentation:** Generates polished, actionable documentation (e.g., READMEs) based on code analysis, rather than simple concatenation.
*   **Advanced Prompting:** Utilizes sophisticated prompt engineering techniques to guide the LLM toward predictable and useful technical output.
*   **Automation Ready:** Designed as a modular CLI tool suitable for integration into CI/CD and static analysis workflows.

## 🛠️ Tech Stack

*   **Language:** Python
*   **Interface:** Command Line Interface (CLI)
*   **LLM Backend:** Ollama (Local LLM Hosting)
*   **Key Libraries:** (Implied dependencies for file system traversal, API calls, etc.)

## 📁 Project Structure

```
.
├── codebase_analyzer/       # Core logic for file discovery and structural mapping.
├── doc_generator/           # Module responsible for prompting and LLM interaction.
├── utils/                   # Helper functions (e.g., token chunking, path normalization).
├── requirements.txt        # Python dependencies list.
└── main.py                  # Entry point for the CLI utility.
```

## 🚀 Setup

1.  **Install Python:** Ensure you have Python 3.8+ installed.
2.  **Install Ollama:** Download and install the Ollama server application.
3.  **Download Model:** Pull a suitable model (e.g., `llama3`) to run locally:
    ```bash
    ollama pull llama3
    ```
4.  **Clone and Install Dependencies:**
    ```bash
    git clone <repository-url>
    cd Codebase-Intelligence-Toolkit
    pip install -r requirements.txt
    ```

## ▶️ Usage

Ensure your Ollama server is running in the background before executing the tool.

To generate documentation for a project located in the `./src/my_app` directory, run the following command:

```bash
python main.py --path ./src/my_app --model llama3 --output README.md
```

**Arguments:**
*   `--path`: The root directory of the codebase to analyze.
*   `--model`: The name of the model hosted in Ollama (e.g., `llama3`).
*   `--output`: The desired filename for the generated documentation.

## 📌 Notes

*   **Ollama Dependency:** The tool is entirely dependent on a locally running Ollama instance accessible via the standard API endpoint.
*   **Prompt Tuning:** Results are heavily dependent on the underlying LLM's capability and the sophistication of the system prompts.
*   **Rate Limiting:** For large codebases, monitor potential API rate limits or process files in batches to ensure stability.
