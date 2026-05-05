from __future__ import annotations

from html import escape
from pathlib import PurePosixPath
import posixpath
import re

from .link_tools import canonical_page_path, resolve_wiki_target
from .utils import strip_model_reasoning


INLINE_CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
WIKI_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")


def markdown_to_html(
    text: str,
    *,
    scope: str = "wiki",
    current_path: str | None = None,
    wiki_lookup: dict[str, str] | None = None,
) -> str:
    text = strip_model_reasoning(text)
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    output: list[str] = []
    paragraph: list[str] = []
    in_code = False
    code_lines: list[str] = []
    code_lang = ""
    list_type: str | None = None
    list_items: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if in_code:
            if stripped.startswith("```"):
                output.append(_render_code_block(code_lines, code_lang))
                in_code = False
                code_lines = []
                code_lang = ""
            else:
                code_lines.append(line)
            i += 1
            continue
        if stripped.startswith("```"):
            _flush_paragraph(output, paragraph, scope, current_path, wiki_lookup)
            _flush_list(output, list_type, list_items)
            list_type = None
            list_items = []
            in_code = True
            code_lang = stripped[3:].strip()
            i += 1
            continue
        if not stripped:
            _flush_paragraph(output, paragraph, scope, current_path, wiki_lookup)
            _flush_list(output, list_type, list_items)
            list_type = None
            list_items = []
            i += 1
            continue
        if stripped in {"---", "***"}:
            _flush_paragraph(output, paragraph, scope, current_path, wiki_lookup)
            _flush_list(output, list_type, list_items)
            list_type = None
            list_items = []
            output.append("<hr>")
            i += 1
            continue
        if stripped.startswith(">"):
            _flush_paragraph(output, paragraph, scope, current_path, wiki_lookup)
            _flush_list(output, list_type, list_items)
            list_type = None
            list_items = []
            quote_lines = [stripped[1:].strip()]
            i += 1
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            quote_text = " ".join(part for part in quote_lines if part)
            output.append(
                f"<blockquote>{_render_inline(quote_text, scope, current_path, wiki_lookup)}</blockquote>"
            )
            continue
        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            _flush_paragraph(output, paragraph, scope, current_path, wiki_lookup)
            _flush_list(output, list_type, list_items)
            list_type = None
            list_items = []
            level = len(heading_match.group(1))
            body = _render_inline(heading_match.group(2), scope, current_path, wiki_lookup)
            output.append(f"<h{level}>{body}</h{level}>")
            i += 1
            continue
        bullet_match = re.match(r"^[-*+]\s+(.*)$", stripped)
        ordered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        if bullet_match or ordered_match:
            _flush_paragraph(output, paragraph, scope, current_path, wiki_lookup)
            next_list_type = "ol" if ordered_match else "ul"
            item_text = ordered_match.group(1) if ordered_match else bullet_match.group(1)
            if list_type and list_type != next_list_type:
                _flush_list(output, list_type, list_items)
                list_items = []
            list_type = next_list_type
            list_items.append(_render_inline(item_text, scope, current_path, wiki_lookup))
            i += 1
            continue
        paragraph.append(stripped)
        i += 1
    if in_code:
        output.append(_render_code_block(code_lines, code_lang))
    _flush_paragraph(output, paragraph, scope, current_path, wiki_lookup)
    _flush_list(output, list_type, list_items)
    return "\n".join(output)


def _flush_paragraph(
    output: list[str],
    paragraph: list[str],
    scope: str,
    current_path: str | None,
    wiki_lookup: dict[str, str] | None,
) -> None:
    if not paragraph:
        return
    body = _render_inline(" ".join(paragraph), scope, current_path, wiki_lookup)
    output.append(f"<p>{body}</p>")
    paragraph.clear()


def _flush_list(output: list[str], list_type: str | None, list_items: list[str]) -> None:
    if not list_type or not list_items:
        return
    items = "".join(f"<li>{item}</li>" for item in list_items)
    output.append(f"<{list_type}>{items}</{list_type}>")
    list_items.clear()


def _render_code_block(lines: list[str], lang: str) -> str:
    class_attr = f' class="language-{escape(lang)}"' if lang else ""
    return f"<pre><code{class_attr}>{escape(chr(10).join(lines))}</code></pre>"


def _render_inline(
    text: str,
    scope: str,
    current_path: str | None,
    wiki_lookup: dict[str, str] | None,
) -> str:
    rendered = escape(text)
    rendered = WIKI_LINK_RE.sub(
        lambda match: _render_wiki_link(match.group(1), wiki_lookup),
        rendered,
    )
    rendered = LINK_RE.sub(
        lambda match: _render_standard_link(match.group(1), match.group(2), scope, current_path),
        rendered,
    )
    rendered = INLINE_CODE_RE.sub(lambda match: f"<code>{escape(match.group(1))}</code>", rendered)
    rendered = BOLD_RE.sub(r"<strong>\1</strong>", rendered)
    rendered = ITALIC_RE.sub(r"<em>\1</em>", rendered)
    return rendered


def _render_standard_link(text: str, href: str, scope: str, current_path: str | None) -> str:
    if href.startswith(("http://", "https://", "mailto:")):
        return f'<a href="{escape(href)}" target="_blank" rel="noreferrer">{text}</a>'
    if href.endswith(".md") or "/" in href:
        resolved = _resolve_relative_path(href, current_path)
        return (
            f'<a href="#" class="internal-link" data-scope="{escape(scope)}" '
            f'data-path="{escape(resolved)}">{text}</a>'
        )
    return f'<a href="{escape(href)}">{text}</a>'


def _render_wiki_link(target: str, wiki_lookup: dict[str, str] | None) -> str:
    label = target
    path = target
    if "|" in target:
        path, label = [part.strip() for part in target.split("|", 1)]
    resolved = resolve_wiki_target(path, wiki_lookup or {}) if wiki_lookup else None
    if not resolved:
        resolved = canonical_page_path(path)
    return (
        f'<a href="#" class="wiki-link internal-link" data-scope="wiki" '
        f'data-path="{escape(resolved)}">{escape(label)}</a>'
    )


def _resolve_relative_path(target: str, current_path: str | None) -> str:
    pure_target = PurePosixPath(target)
    if pure_target.is_absolute() or current_path is None:
        return posixpath.normpath(pure_target.as_posix()).lstrip("/")
    base = PurePosixPath(current_path).parent
    return posixpath.normpath((base / pure_target).as_posix()).lstrip("/")
