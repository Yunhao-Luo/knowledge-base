from __future__ import annotations

from pathlib import Path
import shutil

from .config import AppConfig
from .utils import read_textish, slugify, utc_day


class KnowledgeBase:
    def __init__(self, config: AppConfig):
        self.config = config
        self.root = config.knowledge.root
        self.raw_dir = self.root / "raw"
        self.wiki_dir = self.root / "wiki"
        self.schema_path = config.knowledge.schema_file
        self.index_path = self.wiki_dir / "index.md"
        self.log_path = self.wiki_dir / "log.md"

    def ensure_layout(self) -> None:
        for path in (self.raw_dir, self.wiki_dir, self.schema_path.parent):
            path.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self.index_path.write_text("# Index\n", encoding="utf-8")
        if not self.log_path.exists():
            self.log_path.write_text("# Log\n", encoding="utf-8")
        if not self.schema_path.exists():
            self.schema_path.write_text("# LLM Wiki Schema\n", encoding="utf-8")

    def import_source(self, source_path: Path) -> Path:
        try:
            source_path.resolve().relative_to(self.raw_dir.resolve())
            return source_path
        except ValueError:
            pass
        target_name = source_path.name
        target = self.raw_dir / target_name
        if target.exists():
            target = self.raw_dir / f"{source_path.stem}-{utc_day()}{source_path.suffix}"
        shutil.copy2(source_path, target)
        return target

    def read_source_text(self, path: Path) -> str | None:
        return read_textish(path, self.config.runtime.max_source_chars)

    def raw_sources(self) -> list[Path]:
        return sorted(path for path in self.raw_dir.rglob("*") if path.is_file())

    def wiki_pages(self) -> list[Path]:
        return sorted(
            path for path in self.wiki_dir.rglob("*.md") if path.name not in {"index.md", "log.md"}
        )

    def read_wiki_pages(self) -> dict[Path, str]:
        pages: dict[Path, str] = {}
        for path in self.wiki_pages():
            pages[path] = path.read_text(encoding="utf-8")[: self.config.runtime.max_page_chars]
        return pages

    def read_all_wiki_markdown(self) -> dict[str, str]:
        pages: dict[str, str] = {}
        for path in sorted(self.wiki_dir.rglob("*.md")):
            pages[path.relative_to(self.wiki_dir).as_posix()] = path.read_text(encoding="utf-8")
        return pages

    def write_page(self, relative_path: str, content: str) -> Path:
        target = self.wiki_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content.rstrip() + "\n", encoding="utf-8")
        return target

    def append_log(self, title: str, body: str) -> None:
        entry = f"\n## [{utc_day()}] {title}\n\n{body.strip()}\n"
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(entry)

    def rebuild_index(self) -> None:
        lines = ["# Index", "", "## Wiki Pages", ""]
        for path in self.wiki_pages():
            rel = path.relative_to(self.wiki_dir)
            summary = first_summary_line(path.read_text(encoding="utf-8"))
            lines.append(f"- [{rel.stem}]({rel.as_posix()}) - {summary}")
        self.index_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    def has_source_summary_for(self, raw_path: Path) -> bool:
        return (self.wiki_dir / suggested_source_page(raw_path)).exists()

    def pending_raw_sources(self) -> list[Path]:
        pending: list[Path] = []
        for path in self.raw_sources():
            if path.suffix.lower() not in {".md", ".markdown", ".txt"}:
                continue
            if not self.has_source_summary_for(path):
                pending.append(path)
        return pending


def first_summary_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return stripped[:140]
    return "No summary yet."


def suggested_source_page(raw_path: Path) -> str:
    base = slugify(raw_path.stem)
    return f"sources/{base}.md"
