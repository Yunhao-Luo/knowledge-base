import tempfile
import unittest
from pathlib import Path

from llm_wiki.config import AppConfig, KnowledgeConfig, ProviderConfig, RuntimeConfig
from llm_wiki.gui import WikiGuiApp
from llm_wiki.markdown_render import markdown_to_html
from llm_wiki.assistant import WikiAssistant


class GuiTests(unittest.TestCase):
    def build_config(self, root: Path) -> AppConfig:
        return AppConfig(
            provider=ProviderConfig(kind="command", model="fake", command="fake"),
            knowledge=KnowledgeConfig(root=root, schema_file=root / "schema" / "AGENTS.md"),
            runtime=RuntimeConfig(),
            config_path=root / "config.toml",
        )

    def test_markdown_renderer_builds_internal_wiki_link(self) -> None:
        html = markdown_to_html(
            "See [[Reality Promises paper]] and [overview](../overview.md).",
            scope="wiki",
            current_path="concepts/example.md",
            wiki_lookup={
                "reality-promises-paper": "sources/reality-promises.md",
                "overview": "overview.md",
            },
        )
        self.assertIn('data-path="sources/reality-promises.md"', html)
        self.assertIn('data-path="overview.md"', html)

    def test_markdown_renderer_hides_thinking_tokens(self) -> None:
        html = markdown_to_html("<think>internal reasoning</think>\n# Visible\nBody.")
        self.assertNotIn("internal reasoning", html)
        self.assertIn("Visible", html)

    def test_gui_lists_markdown_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "knowledge"
            config = self.build_config(root)
            assistant = WikiAssistant(config, None)
            assistant.kb.write_page("concepts/example.md", "# Example\nBody.\n")
            raw_file = root / "raw" / "sample.md"
            raw_file.parent.mkdir(parents=True, exist_ok=True)
            raw_file.write_text("# Sample\nBody.\n", encoding="utf-8")
            app = WikiGuiApp(assistant, provider_available=False, provider_error="missing")
            wiki_files = app._list_files("wiki")
            raw_files = app._list_files("raw")
            self.assertTrue(any(item["path"] == "concepts/example.md" for item in wiki_files))
            self.assertTrue(any(item["path"] == "sample.md" for item in raw_files))

    def test_gui_file_payload_resolves_alias_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "knowledge"
            config = self.build_config(root)
            assistant = WikiAssistant(config, None)
            assistant.kb.write_page("sources/reality-promises.md", "# Reality Promises\nBody.\n")
            app = WikiGuiApp(assistant, provider_available=False, provider_error="missing")
            payload = app._file_payload("wiki", "Reality Promises paper")
            self.assertEqual(payload["path"], "sources/reality-promises.md")
            self.assertIn("Reality Promises", payload["html"])


if __name__ == "__main__":
    unittest.main()
