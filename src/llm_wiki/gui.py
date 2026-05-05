from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import parse_qs, urlparse

from .assistant import WikiAssistant
from .knowledge import KnowledgeBase, first_summary_line
from .link_tools import build_wiki_alias_lookup, resolve_wiki_target
from .markdown_render import markdown_to_html
from .models import IngestPlan, LintReport, WikiUpdate


WEB_DIR = Path(__file__).with_name("web")


class WikiGuiApp:
    def __init__(self, assistant: WikiAssistant, provider_available: bool, provider_error: str | None = None):
        self.assistant = assistant
        self.kb: KnowledgeBase = assistant.kb
        self.provider_available = provider_available
        self.provider_error = provider_error
        self._lock = Lock()

    def create_server(self, host: str, port: int) -> ThreadingHTTPServer:
        app = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                app.handle_get(self)

            def do_POST(self) -> None:  # noqa: N802
                app.handle_post(self)

            def log_message(self, format: str, *args) -> None:  # noqa: A003
                return

        return ThreadingHTTPServer((host, port), Handler)

    def handle_get(self, handler: BaseHTTPRequestHandler) -> None:
        parsed = urlparse(handler.path)
        if parsed.path == "/":
            return self._serve_static(handler, "index.html", "text/html; charset=utf-8")
        if parsed.path == "/app.css":
            return self._serve_static(handler, "app.css", "text/css; charset=utf-8")
        if parsed.path == "/app.js":
            return self._serve_static(handler, "app.js", "application/javascript; charset=utf-8")
        if parsed.path == "/api/bootstrap":
            return self._send_json(
                handler,
                self._bootstrap_payload(),
            )
        if parsed.path == "/api/files":
            scope = self._query_value(parsed.query, "scope", "wiki")
            return self._send_json(handler, {"files": self._list_files(scope)})
        if parsed.path == "/api/file":
            scope = self._query_value(parsed.query, "scope", "wiki")
            relative_path = self._query_value(parsed.query, "path", "")
            return self._send_json(handler, self._file_payload(scope, relative_path))
        return self._send_error(handler, HTTPStatus.NOT_FOUND, "Not found")

    def handle_post(self, handler: BaseHTTPRequestHandler) -> None:
        parsed = urlparse(handler.path)
        payload = self._read_json(handler)
        if parsed.path == "/api/action/query":
            return self._run_action(handler, lambda: self._query_payload(payload))
        if parsed.path == "/api/action/ingest":
            return self._run_action(handler, lambda: self._ingest_payload(payload))
        if parsed.path == "/api/action/lint":
            return self._run_action(handler, lambda: self._lint_payload(payload))
        return self._send_error(handler, HTTPStatus.NOT_FOUND, "Not found")

    def _serve_static(self, handler: BaseHTTPRequestHandler, filename: str, content_type: str) -> None:
        path = WEB_DIR / filename
        if not path.exists():
            return self._send_error(handler, HTTPStatus.NOT_FOUND, "Asset not found")
        body = path.read_bytes()
        handler.send_response(HTTPStatus.OK)
        handler.send_header("Content-Type", content_type)
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    def _bootstrap_payload(self) -> dict:
        return {
            "status": self._status_payload(),
            "wikiFiles": self._list_files("wiki"),
            "rawFiles": self._list_files("raw"),
            "pendingSources": [path.relative_to(self.kb.raw_dir).as_posix() for path in self.kb.pending_raw_sources()],
        }

    def _status_payload(self) -> dict:
        return {
            "knowledgeRoot": self.kb.root.as_posix(),
            "rawSourceCount": len(self.kb.raw_sources()),
            "pendingSourceCount": len(self.kb.pending_raw_sources()),
            "wikiPageCount": len(self.kb.wiki_pages()) + 2,
            "providerAvailable": self.provider_available,
            "providerError": self.provider_error,
        }

    def _list_files(self, scope: str) -> list[dict]:
        base = self._scope_base(scope)
        entries: list[dict] = []
        for path in sorted(base.rglob("*.md")):
            relative_path = path.relative_to(base).as_posix()
            entries.append(
                {
                    "scope": scope,
                    "path": relative_path,
                    "name": path.stem.replace("-", " "),
                    "summary": first_summary_line(path.read_text(encoding="utf-8")),
                }
            )
        return entries

    def _file_payload(self, scope: str, relative_path: str) -> dict:
        resolved_path = relative_path
        wiki_lookup: dict[str, str] | None = None
        if scope == "wiki":
            wiki_pages = self.kb.read_all_wiki_markdown()
            wiki_lookup, _ = build_wiki_alias_lookup(wiki_pages)
            resolved_path = self._resolve_wiki_path(relative_path, wiki_pages, wiki_lookup)
        file_path = self._resolve_scope_path(scope, resolved_path)
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(relative_path)
        markdown = file_path.read_text(encoding="utf-8")
        return {
            "scope": scope,
            "path": resolved_path,
            "markdown": markdown,
            "html": markdown_to_html(
                markdown,
                scope=scope,
                current_path=resolved_path,
                wiki_lookup=wiki_lookup or self._wiki_lookup(),
            ),
        }

    def _query_payload(self, payload: dict) -> dict:
        question = str(payload.get("question", "")).strip()
        if not question:
            raise ValueError("Query text is required.")
        with self._lock:
            answer = self.assistant.query(question)
        return {
            "type": "query",
            "markdown": answer,
            "html": markdown_to_html(answer, scope="wiki", wiki_lookup=self._wiki_lookup()),
        }

    def _ingest_payload(self, payload: dict) -> dict:
        ingest_all = bool(payload.get("all"))
        with self._lock:
            if ingest_all:
                plans = self.assistant.ingest_pending()
            else:
                source = str(payload.get("source", "")).strip()
                if not source:
                    raise ValueError("A source path is required.")
                source_path = Path(source)
                if not source_path.is_absolute():
                    source_path = (self.kb.root.parent / source_path).resolve()
                plans = [self.assistant.ingest(source_path)]
        return {
            "type": "ingest",
            "plans": [self._plan_payload(plan) for plan in plans],
            "pendingSources": [path.relative_to(self.kb.raw_dir).as_posix() for path in self.kb.pending_raw_sources()],
            "status": self._status_payload(),
        }

    def _lint_payload(self, payload: dict) -> dict:
        apply = bool(payload.get("apply"))
        with self._lock:
            report = self.assistant.lint(apply=apply)
        return {
            "type": "lint",
            "report": self._report_payload(report),
            "status": self._status_payload(),
        }

    def _plan_payload(self, plan: IngestPlan) -> dict:
        return {
            "sourceSummaryPath": plan.source_summary_path,
            "sourceSummaryMarkdown": plan.source_summary_markdown,
            "wikiUpdates": [self._update_payload(update) for update in plan.wiki_updates],
            "logTitle": plan.log_title,
            "logBody": plan.log_body,
            "assistantNotes": plan.assistant_notes,
        }

    def _report_payload(self, report: LintReport) -> dict:
        return {
            "summary": report.summary,
            "findings": report.findings,
            "suggestedPages": report.suggested_pages,
            "wikiUpdates": [self._update_payload(update) for update in report.wiki_updates],
            "assistantNotes": report.assistant_notes,
        }

    @staticmethod
    def _update_payload(update: WikiUpdate) -> dict:
        return {
            "path": update.path,
            "summary": update.summary,
            "content": update.content,
        }

    @staticmethod
    def _query_value(query: str, key: str, default: str) -> str:
        return parse_qs(query).get(key, [default])[0]

    @staticmethod
    def _read_json(handler: BaseHTTPRequestHandler) -> dict:
        content_length = int(handler.headers.get("Content-Length", "0"))
        raw = handler.rfile.read(content_length) if content_length else b"{}"
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _run_action(self, handler: BaseHTTPRequestHandler, action) -> None:
        try:
            if not self.provider_available:
                raise RuntimeError(self.provider_error or "No provider configured.")
            payload = action()
            self._send_json(handler, payload)
        except FileNotFoundError as exc:
            self._send_error(handler, HTTPStatus.NOT_FOUND, str(exc))
        except Exception as exc:  # noqa: BLE001
            self._send_error(handler, HTTPStatus.BAD_REQUEST, str(exc))

    def _send_json(self, handler: BaseHTTPRequestHandler, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    def _send_error(self, handler: BaseHTTPRequestHandler, status: HTTPStatus, message: str) -> None:
        self._send_json(handler, {"error": message}, status)

    def _scope_base(self, scope: str) -> Path:
        if scope == "wiki":
            return self.kb.wiki_dir
        if scope == "raw":
            return self.kb.raw_dir
        raise ValueError(f"Unsupported scope: {scope}")

    def _resolve_scope_path(self, scope: str, relative_path: str) -> Path:
        base = self._scope_base(scope).resolve()
        target = (base / relative_path).resolve()
        target.relative_to(base)
        return target

    @staticmethod
    def _resolve_wiki_path(relative_path: str, wiki_pages: dict[str, str], wiki_lookup: dict[str, str]) -> str:
        normalized = relative_path.strip().replace("\\", "/").lstrip("/")
        if normalized in wiki_pages:
            return normalized
        resolved = resolve_wiki_target(normalized, wiki_lookup)
        if resolved:
            return resolved
        raise FileNotFoundError(relative_path)

    def _wiki_lookup(self) -> dict[str, str]:
        pages = self.kb.read_all_wiki_markdown()
        lookup, _ = build_wiki_alias_lookup(pages)
        return lookup
