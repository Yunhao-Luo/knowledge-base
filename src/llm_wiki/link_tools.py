from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
import posixpath
import re

from .utils import slugify


WIKI_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")

FOLDER_PRIORITY = {
    "concepts": 0,
    "analyses": 1,
    "entities": 2,
    "projects": 3,
    "sources": 4,
}


@dataclass(slots=True)
class BrokenLink:
    source_path: str
    target: str
    reason: str
    suggestion: str | None = None


def normalize_link_target(target: str) -> str:
    value = target.strip()
    if "|" in value:
        value = value.split("|", 1)[0].strip()
    if "#" in value:
        value = value.split("#", 1)[0].strip()
    value = value.replace("\\", "/").lstrip("/")
    if not value:
        return ""
    parts: list[str] = []
    for raw_part in value.split("/"):
        part = raw_part.strip()
        if not part or part == ".":
            continue
        if part == "..":
            parts.append(part)
            continue
        if part.endswith(".md"):
            part = part[:-3]
        parts.append(slugify(part))
    if not parts:
        return ""
    return posixpath.normpath("/".join(parts)).lower()


def canonical_page_path(target: str) -> str:
    normalized = normalize_link_target(target)
    return f"{normalized}.md" if not normalized.endswith(".md") else normalized


def build_wiki_alias_lookup(pages: dict[str, str]) -> tuple[dict[str, str], dict[str, list[str]]]:
    candidates: dict[str, set[str]] = defaultdict(set)
    for relative_path, markdown in pages.items():
        for alias in _alias_candidates(relative_path, markdown):
            candidates[alias].add(relative_path)
    lookup: dict[str, str] = {}
    ambiguities: dict[str, list[str]] = {}
    for alias, paths in candidates.items():
        ranked = sorted(paths, key=_path_priority)
        lookup[alias] = ranked[0]
        if len(ranked) > 1:
            ambiguities[alias] = ranked
    return lookup, ambiguities


def scan_broken_links(pages: dict[str, str]) -> list[BrokenLink]:
    lookup, ambiguities = build_wiki_alias_lookup(pages)
    findings: list[BrokenLink] = []
    seen: set[tuple[str, str, str]] = set()
    for source_path, markdown in pages.items():
        if source_path == "log.md":
            continue
        for target in extract_internal_targets(markdown):
            resolution = resolve_wiki_target(target, lookup, source_path=source_path)
            if resolution is None:
                suggestion = best_guess_target(target, lookup)
                key = (source_path, target, "missing")
                if key not in seen:
                    findings.append(
                        BrokenLink(
                            source_path=source_path,
                            target=target,
                            reason="missing",
                            suggestion=suggestion,
                        )
                    )
                    seen.add(key)
                continue
            normalized = normalize_link_target(target)
            if normalized in ambiguities and "/" not in normalize_link_target(target):
                key = (source_path, target, "ambiguous")
                if key not in seen:
                    findings.append(
                        BrokenLink(
                            source_path=source_path,
                            target=target,
                            reason="ambiguous",
                            suggestion=lookup[normalized],
                        )
                    )
                    seen.add(key)
    return findings


def apply_link_fixes(wiki_dir: Path) -> list[str]:
    pages = load_wiki_pages(wiki_dir)
    lookup, ambiguities = build_wiki_alias_lookup(pages)
    changed: list[str] = []
    for relative_path, markdown in pages.items():
        if relative_path == "log.md":
            continue
        updated = markdown
        updated = WIKI_LINK_RE.sub(
            lambda match: _rewrite_wiki_link(match.group(1), lookup, ambiguities),
            updated,
        )
        updated = MD_LINK_RE.sub(
            lambda match: _rewrite_markdown_link(relative_path, match.group(1), match.group(2), lookup),
            updated,
        )
        if updated != markdown:
            (wiki_dir / relative_path).write_text(updated, encoding="utf-8")
            changed.append(relative_path)
    return changed


def load_wiki_pages(wiki_dir: Path) -> dict[str, str]:
    return {
        path.relative_to(wiki_dir).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(wiki_dir.rglob("*.md"))
    }


def extract_internal_targets(markdown: str) -> list[str]:
    markdown = _strip_code_regions(markdown)
    targets: list[str] = []
    for match in WIKI_LINK_RE.finditer(markdown):
        targets.append(match.group(1))
    for match in MD_LINK_RE.finditer(markdown):
        href = match.group(2)
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        if href.endswith(".md") or "/" in href:
            targets.append(href)
    return targets


def resolve_wiki_target(target: str, lookup: dict[str, str], source_path: str | None = None) -> str | None:
    relative_candidate = _relative_target_alias(source_path, target)
    if relative_candidate and relative_candidate in lookup:
        return lookup[relative_candidate]
    normalized = normalize_link_target(target)
    if normalized in lookup:
        return lookup[normalized]
    canonical = canonical_page_path(target).lower()
    if canonical.endswith(".md"):
        without_ext = canonical[:-3]
        if without_ext in lookup:
            return lookup[without_ext]
    return None


def best_guess_target(target: str, lookup: dict[str, str]) -> str | None:
    normalized = normalize_link_target(target)
    options = [alias for alias in lookup if normalized in alias or alias in normalized]
    if not options:
        return None
    best = sorted(options, key=lambda item: (abs(len(item) - len(normalized)), item))[0]
    return lookup[best]


def _alias_candidates(relative_path: str, markdown: str) -> set[str]:
    path = PurePosixPath(relative_path)
    no_ext = path.with_suffix("").as_posix()
    stem = path.stem
    aliases = {
        normalize_link_target(relative_path),
        normalize_link_target(no_ext),
        normalize_link_target(stem),
        normalize_link_target(slugify(stem)),
    }
    if path.parent.as_posix() == "sources":
        aliases.add(normalize_link_target(f"{stem} paper"))
    title = first_heading(markdown)
    if title:
        aliases.add(normalize_link_target(title))
    return aliases


def first_heading(markdown: str) -> str | None:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _path_priority(relative_path: str) -> tuple[int, str]:
    path = PurePosixPath(relative_path)
    folder = path.parent.parts[0] if path.parent.parts else ""
    return (FOLDER_PRIORITY.get(folder, 99), relative_path)


def _rewrite_wiki_link(target: str, lookup: dict[str, str], ambiguities: dict[str, list[str]]) -> str:
    raw_target = target
    label = None
    if "|" in raw_target:
        raw_target, label = [part.strip() for part in raw_target.split("|", 1)]
    normalized = normalize_link_target(raw_target)
    if "/" in normalized:
        return f"[[{target}]]"
    resolved = resolve_wiki_target(raw_target, lookup)
    if not resolved:
        return f"[[{target}]]"
    canonical = PurePosixPath(resolved).with_suffix("").as_posix()
    if normalized in ambiguities or canonical != normalized:
        return f"[[{canonical}|{label or raw_target}]]"
    return f"[[{target}]]"


def _rewrite_markdown_link(source_path: str, text: str, href: str, lookup: dict[str, str]) -> str:
    if href.startswith(("http://", "https://", "mailto:")):
        return f"[{text}]({href})"
    normalized_href = normalize_link_target(href)
    resolved = resolve_wiki_target(href, lookup, source_path=source_path)
    if not resolved:
        return f"[{text}]({href})"
    source_dir = PurePosixPath(source_path).parent
    target_rel = posixpath.relpath(resolved, start=source_dir.as_posix() or ".")
    fixed_href = target_rel if target_rel.endswith(".md") else f"{target_rel}.md"
    if fixed_href == href and normalized_href == normalize_link_target(resolved):
        return f"[{text}]({href})"
    return f"[{text}]({fixed_href})"


def _relative_target_alias(source_path: str | None, target: str) -> str | None:
    if source_path is None:
        return None
    candidate = target.strip().replace("\\", "/")
    if "#" in candidate:
        candidate = candidate.split("#", 1)[0].strip()
    if not candidate or not candidate.startswith("."):
        return None
    source_dir = PurePosixPath(source_path).parent
    resolved = posixpath.normpath((source_dir / PurePosixPath(candidate)).as_posix()).lstrip("/")
    return normalize_link_target(resolved)


def _strip_code_regions(markdown: str) -> str:
    without_blocks = CODE_BLOCK_RE.sub("", markdown)
    return INLINE_CODE_RE.sub("", without_blocks)
