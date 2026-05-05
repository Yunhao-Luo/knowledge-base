import tempfile
import unittest
from pathlib import Path

from llm_wiki.link_tools import apply_link_fixes, scan_broken_links


class LinkToolsTests(unittest.TestCase):
    def test_scan_broken_links_resolves_relative_markdown_paths(self) -> None:
        pages = {
            "overview.md": "# Overview\nTop page.\n",
            "concepts/example.md": "# Example\nSee [overview](../overview.md).\n",
        }
        findings = scan_broken_links(pages)
        self.assertEqual(findings, [])

    def test_scan_broken_links_flags_ambiguous_aliases(self) -> None:
        pages = {
            "concepts/xr-ai-intersection.md": "# XR AI Intersection\nConcept view.\n",
            "analyses/xr-ai-intersection.md": "# XR AI Intersection\nAnalysis view.\n",
            "overview.md": "# Overview\nSee [[xr-ai-intersection]].\n",
        }
        findings = scan_broken_links(pages)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].reason, "ambiguous")
        self.assertEqual(findings[0].suggestion, "concepts/xr-ai-intersection.md")

    def test_apply_link_fixes_rewrites_ambiguous_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = Path(tmp)
            (wiki_dir / "concepts").mkdir()
            (wiki_dir / "sources").mkdir()
            (wiki_dir / "analyses").mkdir()
            (wiki_dir / "concepts" / "reality-promises.md").write_text(
                "# Reality Promises\nConcept page.\n",
                encoding="utf-8",
            )
            (wiki_dir / "sources" / "reality-promises.md").write_text(
                "# Reality Promises\nSource page.\n",
                encoding="utf-8",
            )
            target = wiki_dir / "analyses" / "example.md"
            target.write_text("# Example\nSee [[reality-promises]].\n", encoding="utf-8")

            changed = apply_link_fixes(wiki_dir)

            self.assertEqual(changed, ["analyses/example.md"])
            self.assertIn(
                "[[concepts/reality-promises|reality-promises]]",
                target.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
