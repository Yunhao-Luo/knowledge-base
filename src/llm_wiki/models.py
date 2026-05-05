from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CompletionResult:
    text: str


@dataclass(slots=True)
class WikiUpdate:
    path: str
    content: str
    summary: str


@dataclass(slots=True)
class IngestPlan:
    source_summary_path: str
    source_summary_markdown: str
    wiki_updates: list[WikiUpdate] = field(default_factory=list)
    log_title: str = ""
    log_body: str = ""
    assistant_notes: str = ""


@dataclass(slots=True)
class LintReport:
    summary: str
    findings: list[str]
    suggested_pages: list[str]
    wiki_updates: list[WikiUpdate] = field(default_factory=list)
    assistant_notes: str = ""
