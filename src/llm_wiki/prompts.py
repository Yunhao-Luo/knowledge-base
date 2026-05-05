INGEST_SYSTEM = """You maintain a persistent markdown wiki from source material.
Return the exact tagged text format requested. Do not wrap it in markdown fences.
"""

INGEST_PROMPT = """Schema:
{schema}

Current index:
{index}

Relevant existing pages:
{pages}

Source file: {source_name}
Raw source path: {source_path}

Source contents:
{source_text}

Return output in exactly this tagged format:

SOURCE_SUMMARY_PATH: sources/example.md
LOG_TITLE: ingest | source title
LOG_BODY:
2-5 sentence summary of what changed in the wiki.
END_LOG_BODY
ASSISTANT_NOTES:
short note to the human about contradictions, follow-up questions, or caveats
END_ASSISTANT_NOTES
BEGIN_SOURCE_SUMMARY
# Title
...
END_SOURCE_SUMMARY
BEGIN_WIKI_UPDATE
PATH: concepts/example.md
SUMMARY: one line summary for index
CONTENT:
# Example
...
END_CONTENT
END_WIKI_UPDATE

You may repeat BEGIN_WIKI_UPDATE ... END_WIKI_UPDATE blocks as needed.

Rules:
- Prefer updating a small number of high-value pages over many shallow pages.
- Use full markdown content for each page, not diffs.
- Include source citations inside pages using normal markdown links to the source summary page when appropriate.
- If the source conflicts with existing pages, explicitly note that in the relevant page content.
"""

QUERY_SYSTEM = """You answer questions against a markdown wiki.
Use the provided pages as your source of truth and cite page paths inline.
"""

QUERY_PROMPT = """Question:
{question}

Index:
{index}

Relevant pages:
{pages}

Answer clearly and cite the wiki page path in parentheses for major claims.
If the answer reveals a durable insight worth storing, end with a line starting with 'SAVE_SUGGESTION:'.
"""

LINT_SYSTEM = """You are checking a markdown wiki for maintenance issues.
Return valid JSON only. Do not wrap it in markdown fences.
"""

LINT_PROMPT = """Schema:
{schema}

Index:
{index}

Wiki pages:
{pages}

Return JSON with this shape:
{{
  "summary": "short overview",
  "findings": ["issue 1", "issue 2"],
  "suggested_pages": ["concepts/example.md", "entities/example.md"]
}}
"""

LINT_APPLY_SYSTEM = """You are repairing a markdown wiki based on a lint pass.
Return valid JSON only. Do not wrap it in markdown fences.
"""

LINT_APPLY_PROMPT = """Schema:
{schema}

Index:
{index}

Wiki pages:
{pages}

Produce JSON with this shape:
{{
  "summary": "short overview of applied fixes",
  "findings": ["issue 1", "issue 2"],
  "suggested_pages": ["concepts/example.md"],
  "wiki_updates": [
    {{
      "path": "concepts/example.md",
      "summary": "short summary",
      "content": "# Example\\n..."
    }}
  ],
  "assistant_notes": "short note about remaining manual follow-up"
}}

Rules:
- Fix concrete wiki issues directly when possible.
- Return full page contents, not diffs.
- Preserve existing useful content unless it is clearly wrong or stale.
- If a page should be created, include it in wiki_updates.
- If no page changes are needed, return an empty wiki_updates list.
"""

LINT_CREATE_MISSING_SYSTEM = """You are creating missing markdown wiki pages identified during a lint repair pass.
Return valid JSON only. Do not wrap it in markdown fences.
"""

LINT_CREATE_MISSING_PROMPT = """Schema:
{schema}

Index:
{index}

Wiki pages:
{pages}

Create full markdown pages for these missing wiki paths:
{missing_paths}

Return JSON with this shape:
{{
  "wiki_updates": [
    {{
      "path": "concepts/example.md",
      "summary": "short summary",
      "content": "# Example\\n..."
    }}
  ],
  "assistant_notes": "short note about what was created"
}}

Rules:
- Create every requested page unless there is truly not enough information.
- Return full page contents, not diffs.
- Use concise, factual starter pages with links to related existing pages.
- If information is limited, create a stub page that says what the concept is and how it relates to the current wiki.
"""
