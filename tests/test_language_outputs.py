"""Integration checks for conversational formatting and content."""
from __future__ import annotations

import unittest

from eidolon_prime import EidolonPrimeApp


class LanguageOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = EidolonPrimeApp.from_config_path(None)
        cls.app.kernel.bootstrap()

    def _paragraphs(self, text: str) -> list[str]:
        return [segment.strip() for segment in text.split("\n\n") if segment.strip()]

    def test_essay_requests_yield_multi_paragraph_output(self) -> None:
        result = self.app.kernel.chat(
            "Please write a multi-paragraph essay on ethical Roblox economy design."
        )
        paragraphs = self._paragraphs(result.reply)
        self.assertGreaterEqual(
            len(paragraphs), 4, "Essay replies should include several paragraphs."
        )
        total_words = sum(len(paragraph.split()) for paragraph in paragraphs)
        self.assertGreaterEqual(
            total_words,
            60,
            "Essay replies should accumulate a meaningful amount of prose.",
        )

    def test_roblox_script_prompts_include_multiline_snippet(self) -> None:
        result = self.app.kernel.chat(
            "Can you share a Roblox script that manages quest publication?"
        )
        self.assertIn("```lua", result.reply)
        self.assertIn(
            "\nfunction", result.reply, "Roblox snippet should maintain newline structure."
        )

    def test_world_briefing_uses_situation_evidence_outlook(self) -> None:
        result = self.app.kernel.chat("What is happening in the world today?")
        paragraphs = self._paragraphs(result.reply)
        labels = {"Situation:", "Evidence:", "Implication:", "Outlook:"}
        found = {paragraph.split()[0] for paragraph in paragraphs if ":" in paragraph}
        self.assertTrue(
            labels.issubset(found),
            "World briefings should present situation, evidence, implication, and outlook paragraphs.",
        )


if __name__ == "__main__":
    unittest.main()
