from pathlib import Path
import unittest

from llm_wiki.search import rank_files


class SearchTests(unittest.TestCase):
    def test_rank_files_prefers_relevant_page(self) -> None:
        pages = {
            Path("concepts/memex.md"): "Memex is about associative trails and personal knowledge.",
            Path("projects/travel.md"): "Trip planning notes and hotels.",
        }
        ranked = rank_files("associative trails", pages, limit=2)
        self.assertEqual(ranked[0], Path("concepts/memex.md"))


if __name__ == "__main__":
    unittest.main()
