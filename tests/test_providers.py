import unittest

from llm_wiki.assistant import WikiAssistant
from llm_wiki.providers import ProviderError, parse_openai_style_response
from llm_wiki.utils import strip_model_reasoning


class ProviderParsingTests(unittest.TestCase):
    def test_parses_standard_chat_response(self) -> None:
        body = {"choices": [{"message": {"content": "hello"}}]}
        self.assertEqual(parse_openai_style_response(body), "hello")

    def test_parses_content_array_response(self) -> None:
        body = {
            "choices": [
                {
                    "message": {
                        "content": [
                            {"type": "text", "text": "hello"},
                            {"type": "text", "text": "world"},
                        ]
                    }
                }
            ]
        }
        self.assertEqual(parse_openai_style_response(body), "hello\nworld")

    def test_raises_provider_error_for_error_payload(self) -> None:
        body = {"error": {"message": "No model loaded"}}
        with self.assertRaises(ProviderError):
            parse_openai_style_response(body)

    def test_raises_provider_error_for_string_error_payload(self) -> None:
        body = {"error": "Model 'local-model' not found"}
        with self.assertRaises(ProviderError) as context:
            parse_openai_style_response(body)
        self.assertIn("local-model", str(context.exception))

    def test_parse_wiki_update_accepts_extra_fields_and_aliases(self) -> None:
        update = WikiAssistant._parse_wiki_update(
            {
                "path": "concepts/xr-ai.md",
                "content_updated": "# XR + AI\n",
                "summary": "Updated synthesis.",
                "extra_field": True,
            }
        )
        self.assertEqual(update.path, "concepts/xr-ai.md")
        self.assertEqual(update.content, "# XR + AI\n")
        self.assertEqual(update.summary, "Updated synthesis.")

    def test_parse_json_object_accepts_fenced_json(self) -> None:
        parsed = WikiAssistant._parse_json_object(
            '```json\n{"summary":"ok","findings":[],"suggested_pages":[]}\n```'
        )
        self.assertEqual(parsed["summary"], "ok")

    def test_parse_json_object_accepts_prefixed_json(self) -> None:
        parsed = WikiAssistant._parse_json_object(
            'Here is the result:\n{"summary":"ok","findings":[],"suggested_pages":[]}'
        )
        self.assertEqual(parsed["summary"], "ok")

    def test_parse_json_object_accepts_think_prefixed_json(self) -> None:
        parsed = WikiAssistant._parse_json_object(
            '<think>I should reason first.</think>\n{"summary":"ok","findings":[],"suggested_pages":[]}'
        )
        self.assertEqual(parsed["summary"], "ok")

    def test_parse_ingest_tagged_response(self) -> None:
        parsed = WikiAssistant._parse_ingest_tagged_response(
            """SOURCE_SUMMARY_PATH: sources/example.md
LOG_TITLE: ingest | example
LOG_BODY:
Updated the wiki.
END_LOG_BODY
ASSISTANT_NOTES:
Watch for contradictions.
END_ASSISTANT_NOTES
BEGIN_SOURCE_SUMMARY
# Example
Summary text.
END_SOURCE_SUMMARY
BEGIN_WIKI_UPDATE
PATH: concepts/example.md
SUMMARY: Example concept page.
CONTENT:
# Example
Body text.
END_CONTENT
END_WIKI_UPDATE
"""
        )
        self.assertEqual(parsed["source_summary_path"], "sources/example.md")
        self.assertEqual(parsed["wiki_updates"][0]["path"], "concepts/example.md")

    def test_strip_model_reasoning_handles_unclosed_think_block(self) -> None:
        cleaned = strip_model_reasoning("<think>private chain of thought")
        self.assertEqual(cleaned, "")

    def test_strip_model_reasoning_handles_escaped_think_block(self) -> None:
        cleaned = strip_model_reasoning("&lt;think&gt;private chain of thought&lt;/think&gt;\nVisible")
        self.assertEqual(cleaned, "Visible")

    def test_strip_model_reasoning_handles_think_tag_with_attributes(self) -> None:
        cleaned = strip_model_reasoning('<think type="reasoning">private</think>\nVisible')
        self.assertEqual(cleaned, "Visible")


if __name__ == "__main__":
    unittest.main()
