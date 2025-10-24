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

    def test_interactive_research_is_logged_in_reasoning(self) -> None:
        result = self.app.kernel.chat(
            "Explain advanced Roblox data store sharding strategies for live games."
        )
        self.assertIn(
            "live research",
            result.analysis.reasoning_summary.lower(),
            "Chat reasoning should mention the interactive research sweep.",
        )

    def test_smalltalk_stays_concise_and_personal(self) -> None:
        result = self.app.kernel.chat("Hi, how is your day going?")
        paragraphs = self._paragraphs(result.reply)
        self.assertLessEqual(len(paragraphs), 2, "Small talk replies should stay brief.")
        lowered = result.reply.lower()
        self.assertNotIn("curiosity is high", lowered)
        self.assertNotIn("personality", lowered)

    def test_distillation_command_populates_dialogue_examples(self) -> None:
        receipt = self.app.kernel.distill()
        self.assertGreaterEqual(
            receipt.stored,
            1,
            "Distillation should capture at least one dialogue exemplar.",
        )

    def test_peer_dialogue_cycle_generates_report(self) -> None:
        report = self.app.kernel.peer_dialogue("creative writing warmup")
        self.assertGreaterEqual(
            report.stored,
            2,
            "Peer dialogue cycles should archive multiple utterances.",
        )
        self.assertIn(
            "Peer dialogue",
            report.render(),
            "Peer dialogue report should render a descriptive summary.",
        )

    def test_grammar_rule_inventory_reports_million_rules(self) -> None:
        self.assertGreaterEqual(
            self.app.kernel.grammar_rule_inventory(),
            1_000_000,
            "Grammar datastore should expose at least one million conversational rules.",
        )


if __name__ == "__main__":
    unittest.main()
