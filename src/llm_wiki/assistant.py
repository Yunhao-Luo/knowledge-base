from __future__ import annotations

import json
from pathlib import Path
import re

from .config import AppConfig
from .knowledge import KnowledgeBase, suggested_source_page
from .link_tools import BrokenLink, apply_link_fixes, scan_broken_links
from .models import IngestPlan, LintReport, WikiUpdate
from .prompts import (
    INGEST_PROMPT,
    INGEST_SYSTEM,
    LINT_APPLY_PROMPT,
    LINT_APPLY_SYSTEM,
    LINT_CREATE_MISSING_PROMPT,
    LINT_CREATE_MISSING_SYSTEM,
    LINT_PROMPT,
    LINT_SYSTEM,
    QUERY_PROMPT,
    QUERY_SYSTEM,
)
from .providers import BaseProvider, ProviderError
from .search import rank_files
from .utils import strip_model_reasoning


class WikiAssistant:
    def __init__(self, config: AppConfig, provider: BaseProvider | None):
        self.config = config
        self.provider = provider
        self.kb = KnowledgeBase(config)
        self.kb.ensure_layout()

    def ingest(self, source_path: Path) -> IngestPlan:
        imported = self.kb.import_source(source_path)
        source_text = self.kb.read_source_text(imported)
        if not source_text:
            raise ValueError("Source is not a supported text file for prompt ingestion.")
        pages = self.kb.read_wiki_pages()
        ranked = rank_files(imported.stem, pages, self.config.runtime.max_context_files)
        relevant = self._format_pages({path: pages[path] for path in ranked})
        prompt = INGEST_PROMPT.format(
            schema=self.kb.schema_path.read_text(encoding="utf-8"),
            index=self.kb.index_path.read_text(encoding="utf-8"),
            pages=relevant,
            source_name=imported.name,
            source_path=imported.as_posix(),
            source_text=source_text,
        )
        response = self.require_provider().complete(INGEST_SYSTEM, prompt)
        plan = self._parse_ingest_response(response.text, imported)
        self.kb.write_page(plan.source_summary_path, plan.source_summary_markdown)
        for update in plan.wiki_updates:
            self.kb.write_page(update.path, update.content)
        self.kb.append_log(plan.log_title, plan.log_body)
        self.kb.rebuild_index()
        return plan

    def query(self, question: str) -> str:
        pages = self.kb.read_wiki_pages()
        ranked = rank_files(question, pages, self.config.runtime.max_context_files)
        prompt = QUERY_PROMPT.format(
            question=question,
            index=self.kb.index_path.read_text(encoding="utf-8"),
            pages=self._format_pages({path: pages[path] for path in ranked}),
        )
        response = self.require_provider().complete(QUERY_SYSTEM, prompt)
        self.kb.append_log("query", f"Question: {question}")
        return strip_model_reasoning(response.text)

    def lint(self, apply: bool = False) -> LintReport:
        pages = self.kb.read_wiki_pages()
        if apply:
            return self._lint_apply(pages)
        prompt = LINT_PROMPT.format(
            schema=self.kb.schema_path.read_text(encoding="utf-8"),
            index=self.kb.index_path.read_text(encoding="utf-8"),
            pages=self._format_pages(pages),
        )
        response = self.require_provider().complete(LINT_SYSTEM, prompt)
        data = self._parse_json_object(response.text)
        report = LintReport(
            summary=data["summary"],
            findings=data.get("findings", []),
            suggested_pages=data.get("suggested_pages", []),
        )
        body_lines = [report.summary]
        if report.findings:
            body_lines.extend(f"- {item}" for item in report.findings)
        self.kb.append_log("lint", "\n".join(body_lines))
        return report

    def ingest_many(self, source_paths: list[Path]) -> list[IngestPlan]:
        plans: list[IngestPlan] = []
        for path in source_paths:
            plans.append(self.ingest(path))
        return plans

    def ingest_pending(self) -> list[IngestPlan]:
        return self.ingest_many(self.kb.pending_raw_sources())

    def pending_sources(self) -> list[Path]:
        return self.kb.pending_raw_sources()

    def check_links(self) -> list[BrokenLink]:
        return scan_broken_links(self.kb.read_all_wiki_markdown())

    def fix_links(self) -> tuple[list[str], list[BrokenLink]]:
        changed = apply_link_fixes(self.kb.wiki_dir)
        if changed:
            self.kb.rebuild_index()
            body = "\n".join(f"- rewrote {path}" for path in changed)
            self.kb.append_log("links-fix", body)
        return changed, self.check_links()

    def status(self) -> str:
        return (
            f"Knowledge root: {self.kb.root}\n"
            f"Raw sources: {len(self.kb.raw_sources())}\n"
            f"Pending raw sources: {len(self.kb.pending_raw_sources())}\n"
            f"Wiki pages: {len(self.kb.wiki_pages())}\n"
            f"Schema: {self.kb.schema_path}"
        )

    def require_provider(self) -> BaseProvider:
        if self.provider is None:
            raise ProviderError(
                "No provider is configured for this command. Set API credentials or use a command adapter."
            )
        return self.provider

    @staticmethod
    def _format_pages(pages: dict[Path, str]) -> str:
        if not pages:
            return "(none)"
        chunks: list[str] = []
        for path, text in pages.items():
            chunks.append(f"--- {path.name} ({path.as_posix()}) ---\n{text}")
        return "\n\n".join(chunks)

    @staticmethod
    def _parse_wiki_update(item: dict) -> WikiUpdate:
        if not isinstance(item, dict):
            raise ValueError("Each wiki update must be a JSON object.")
        path = item.get("path") or item.get("file_path")
        content = item.get("content") or item.get("content_updated") or item.get("markdown")
        summary = item.get("summary") or item.get("description") or ""
        if not path:
            raise ValueError("Wiki update is missing a path.")
        if not content:
            raise ValueError(f"Wiki update for {path} is missing content.")
        return WikiUpdate(path=path, content=content, summary=summary)

    def _lint_apply(self, pages: dict[Path, str]) -> LintReport:
        prompt = LINT_APPLY_PROMPT.format(
            schema=self.kb.schema_path.read_text(encoding="utf-8"),
            index=self.kb.index_path.read_text(encoding="utf-8"),
            pages=self._format_pages(pages),
        )
        response = self.require_provider().complete(LINT_APPLY_SYSTEM, prompt)
        data = self._parse_json_object(response.text)
        report = LintReport(
            summary=data["summary"],
            findings=data.get("findings", []),
            suggested_pages=data.get("suggested_pages", []),
            wiki_updates=[self._parse_wiki_update(item) for item in data.get("wiki_updates", [])],
            assistant_notes=data.get("assistant_notes", ""),
        )
        self._fill_missing_lint_pages(report, pages)
        for update in report.wiki_updates:
            self.kb.write_page(update.path, update.content)
        self.kb.rebuild_index()
        body_lines = [report.summary]
        if report.findings:
            body_lines.extend(f"- {item}" for item in report.findings)
        if report.wiki_updates:
            body_lines.append("")
            body_lines.extend(f"- applied {item.path}" for item in report.wiki_updates)
        self.kb.append_log("lint-apply", "\n".join(body_lines))
        return report

    def _fill_missing_lint_pages(self, report: LintReport, pages: dict[Path, str]) -> None:
        existing_paths = {update.path for update in report.wiki_updates}
        missing_paths: list[str] = []
        for path in report.suggested_pages:
            if path in existing_paths:
                continue
            if (self.kb.wiki_dir / path).exists():
                continue
            missing_paths.append(path)
        if not missing_paths:
            return
        prompt = LINT_CREATE_MISSING_PROMPT.format(
            schema=self.kb.schema_path.read_text(encoding="utf-8"),
            index=self.kb.index_path.read_text(encoding="utf-8"),
            pages=self._format_pages(pages),
            missing_paths="\n".join(f"- {path}" for path in missing_paths),
        )
        response = self.require_provider().complete(LINT_CREATE_MISSING_SYSTEM, prompt)
        data = self._parse_json_object(response.text)
        created_updates = [self._parse_wiki_update(item) for item in data.get("wiki_updates", [])]
        report.wiki_updates.extend(
            update for update in created_updates if update.path not in {item.path for item in report.wiki_updates}
        )
        extra_notes = data.get("assistant_notes", "").strip()
        if extra_notes:
            if report.assistant_notes:
                report.assistant_notes = f"{report.assistant_notes}\n\n{extra_notes}"
            else:
                report.assistant_notes = extra_notes

    def _parse_ingest_response(self, text: str, imported: Path) -> IngestPlan:
        try:
            data = self._parse_json_object(text)
        except ValueError:
            data = self._parse_ingest_tagged_response(text)
        return IngestPlan(
            source_summary_path=data.get("source_summary_path") or suggested_source_page(imported),
            source_summary_markdown=data["source_summary_markdown"],
            wiki_updates=[self._parse_wiki_update(item) for item in data.get("wiki_updates", [])],
            log_title=data.get("log_title", f"ingest | {imported.name}"),
            log_body=data.get("log_body", f"Processed source `{imported.name}`."),
            assistant_notes=data.get("assistant_notes", ""),
        )

    @staticmethod
    def _parse_ingest_tagged_response(text: str) -> dict:
        cleaned = WikiAssistant._strip_reasoning_blocks(text).strip()
        if not cleaned:
            raise ValueError("Model returned an empty response where ingest output was expected.")
        source_summary_path = WikiAssistant._extract_line_value(cleaned, "SOURCE_SUMMARY_PATH:")
        source_summary_markdown = WikiAssistant._extract_tag_block(
            cleaned, "BEGIN_SOURCE_SUMMARY", "END_SOURCE_SUMMARY"
        )
        if not source_summary_path or source_summary_markdown is None:
            preview = cleaned[:240].replace("\n", "\\n")
            raise ValueError(
                f"Model did not return a valid ingest response. Response started with: {preview}"
            )
        log_title = WikiAssistant._extract_line_value(cleaned, "LOG_TITLE:")
        log_body = WikiAssistant._extract_tag_block(cleaned, "LOG_BODY:", "END_LOG_BODY") or ""
        assistant_notes = (
            WikiAssistant._extract_tag_block(cleaned, "ASSISTANT_NOTES:", "END_ASSISTANT_NOTES") or ""
        )
        wiki_updates = WikiAssistant._extract_tagged_wiki_updates(cleaned)
        return {
            "source_summary_path": source_summary_path,
            "source_summary_markdown": source_summary_markdown,
            "wiki_updates": wiki_updates,
            "log_title": log_title or "",
            "log_body": log_body,
            "assistant_notes": assistant_notes,
        }

    @staticmethod
    def _parse_json_object(text: str) -> dict:
        cleaned = WikiAssistant._strip_reasoning_blocks(text).strip()
        if not cleaned:
            raise ValueError("Model returned an empty response where JSON was expected.")
        candidates = [cleaned]
        fenced = WikiAssistant._extract_fenced_block(cleaned)
        if fenced:
            candidates.append(fenced)
        braced = WikiAssistant._extract_braced_json(cleaned)
        if braced and braced not in candidates:
            candidates.append(braced)
        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        preview = cleaned[:240].replace("\n", "\\n")
        raise ValueError(f"Model did not return a valid JSON object. Response started with: {preview}")

    @staticmethod
    def _strip_reasoning_blocks(text: str) -> str:
        return strip_model_reasoning(text)

    @staticmethod
    def _extract_line_value(text: str, prefix: str) -> str | None:
        for line in text.splitlines():
            if line.startswith(prefix):
                return line[len(prefix) :].strip()
        return None

    @staticmethod
    def _extract_tag_block(text: str, start_tag: str, end_tag: str) -> str | None:
        start = text.find(start_tag)
        if start == -1:
            return None
        start += len(start_tag)
        if start < len(text) and text[start] == "\n":
            start += 1
        end = text.find(end_tag, start)
        if end == -1:
            return None
        return text[start:end].strip()

    @staticmethod
    def _extract_tagged_wiki_updates(text: str) -> list[dict]:
        updates: list[dict] = []
        marker = "BEGIN_WIKI_UPDATE"
        start = 0
        while True:
            block_start = text.find(marker, start)
            if block_start == -1:
                return updates
            block_end = text.find("END_WIKI_UPDATE", block_start)
            if block_end == -1:
                return updates
            block = text[block_start + len(marker) : block_end].strip()
            path = WikiAssistant._extract_line_value(block, "PATH:")
            summary = WikiAssistant._extract_line_value(block, "SUMMARY:") or ""
            content = WikiAssistant._extract_tag_block(block, "CONTENT:", "END_CONTENT")
            if path and content is not None:
                updates.append({"path": path, "summary": summary, "content": content})
            start = block_end + len("END_WIKI_UPDATE")

    @staticmethod
    def _extract_fenced_block(text: str) -> str | None:
        if "```" not in text:
            return None
        parts = text.split("```")
        if len(parts) < 3:
            return None
        for block in parts[1::2]:
            stripped = block.strip()
            if stripped.startswith("json"):
                return stripped[4:].strip()
            if stripped.startswith("{"):
                return stripped
        return None

    @staticmethod
    def _extract_braced_json(text: str) -> str | None:
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : index + 1]
        return None
