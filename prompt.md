Summarize the repository into a single JSON object for a technical profile or project summary.

Use the repository summary and batch summaries together. The output should describe the whole codebase, not just one visible file or one surface area.

Return only valid JSON with these fields:
{
  "title": "<short repository title>",
  "date": "<year or date if known, otherwise N/A>",
  "description": "<brief summary of the repository>",
  "tags": ["<tag1>", "<tag2>", "<tag3>"],
  "link": "<git link if available, otherwise N/A>"
}

Guidelines:
- Keep the description under 200 words.
- Use simple, clear language.
- Explain the overall purpose of the repository.
- Mention the major modules, tools, or subsystems that make up the project.
- If the repository contains multiple stages or workflows, include them in the description.
- Mention the key flows, behavior, or architecture if visible.
- Mention important dependencies, frameworks, or technologies if visible.
- Do not describe the repository as only one app if it clearly contains several related tools or steps.
- You may refer to languages and modules but do not mention specific file names
- Keep tags short and relevant.
- If a field is unknown, use "N/A" rather than inventing details.
- Do not wrap the JSON in markdown fences.

In the description field focus on what the project does in wording understandable to average people

Example tags:
  "Embedded Systems",
  "FreeRTOS",
  "Computer Vision",
  "PID Control",
  "Robotics",
  "ESP32",
  "CAD"