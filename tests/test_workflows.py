import json
import tempfile
import unittest
from pathlib import Path

from llm_wiki.assistant import WikiAssistant
from llm_wiki.config import AppConfig, KnowledgeConfig, ProviderConfig, RuntimeConfig
from llm_wiki.knowledge import KnowledgeBase
from llm_wiki.models import CompletionResult


class FakeProvider:
    def __init__(self, responses: list[dict]):
        self._responses = list(responses)

    def complete(self, system: str, prompt: str) -> CompletionResult:
        if not self._responses:
            raise AssertionError("No fake responses remaining.")
        return CompletionResult(text=json.dumps(self._responses.pop(0)))


class WorkflowTests(unittest.TestCase):
    def build_config(self, root: Path) -> AppConfig:
        return AppConfig(
            provider=ProviderConfig(kind="command", model="fake", command="fake"),
            knowledge=KnowledgeConfig(root=root, schema_file=root / "schema" / "AGENTS.md"),
            runtime=RuntimeConfig(),
            config_path=root / "config.toml",
        )

    def test_pending_raw_sources_skip_already_ingested_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "knowledge"
            kb = KnowledgeBase(self.build_config(root))
            kb.ensure_layout()
            pending = root / "raw" / "topic-a.md"
            done = root / "raw" / "topic-b.md"
            pending.write_text("# Topic A\n", encoding="utf-8")
            done.write_text("# Topic B\n", encoding="utf-8")
            kb.write_page("sources/topic-b.md", "# Topic B summary\n",)
            self.assertEqual(kb.pending_raw_sources(), [pending])

    def test_lint_apply_writes_updates_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "knowledge"
            config = self.build_config(root)
            kb = KnowledgeBase(config)
            kb.ensure_layout()
            kb.write_page("concepts/example.md", "# Example\nOld content.\n")
            kb.rebuild_index()
            provider = FakeProvider(
                [
                    {
                        "summary": "Applied cleanup.",
                        "findings": ["Fixed broken concept links."],
                        "suggested_pages": [],
                        "wiki_updates": [
                            {
                                "path": "concepts/example.md",
                                "content": "# Example\nNew content.\n",
                                "summary": "Updated example page.",
                            }
                        ],
                        "assistant_notes": "No further action needed.",
                    }
                ]
            )
            assistant = WikiAssistant(config, provider)
            report = assistant.lint(apply=True)
            self.assertEqual(report.summary, "Applied cleanup.")
            self.assertEqual(report.wiki_updates[0].path, "concepts/example.md")
            page_text = (root / "wiki" / "concepts" / "example.md").read_text(encoding="utf-8")
            self.assertIn("New content.", page_text)
            log_text = (root / "wiki" / "log.md").read_text(encoding="utf-8")
            self.assertIn("lint-apply", log_text)

    def test_lint_apply_creates_suggested_missing_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "knowledge"
            config = self.build_config(root)
            kb = KnowledgeBase(config)
            kb.ensure_layout()
            kb.write_page("concepts/xr-ai-intersection.md", "# XR-AI Intersection\nSee [[concepts/virtual-reality]].\n")
            kb.rebuild_index()
            provider = FakeProvider(
                [
                    {
                        "summary": "Fixed links.",
                        "findings": ["virtual-reality page missing."],
                        "suggested_pages": ["concepts/virtual-reality.md"],
                        "wiki_updates": [],
                        "assistant_notes": "Creating missing concepts.",
                    },
                    {
                        "wiki_updates": [
                            {
                                "path": "concepts/virtual-reality.md",
                                "content": "# Virtual Reality\nVirtual reality is an immersive XR mode.\n",
                                "summary": "Starter page for VR.",
                            }
                        ],
                        "assistant_notes": "Created virtual-reality page.",
                    },
                ]
            )
            assistant = WikiAssistant(config, provider)
            report = assistant.lint(apply=True)
            self.assertTrue((root / "wiki" / "concepts" / "virtual-reality.md").exists())
            self.assertIn("Created virtual-reality page.", report.assistant_notes)
            self.assertIn("concepts/virtual-reality.md", [item.path for item in report.wiki_updates])


if __name__ == "__main__":
    unittest.main()
