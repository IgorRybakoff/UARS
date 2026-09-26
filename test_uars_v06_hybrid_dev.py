"""Quote and abstention checks independent of any model provider."""
import unittest
import json
import shlex
import sys
from pathlib import Path

from uars_v06_hybrid_dev import evaluate, validate_judgment
from uars_v06_preflight import run


FRAGMENTS = [{"start": 31, "end": 61,
              "text": "The source states a limit of 72 MHz.", "score": 0.8}]


class SemanticBoundary(unittest.TestCase):
    def test_accepts_only_exact_evidence_quote(self):
        r = validate_judgment({"support_label": "SUPPORTED", "confidence": "high",
                               "evidence_span": "a limit of 72 MHz", "reason": "present"}, FRAGMENTS)
        self.assertEqual(r["support_label"], "SUPPORTED")
        self.assertEqual(r["span_start"], 49)

    def test_rejects_invented_quote(self):
        r = validate_judgment({"support_label": "SUPPORTED", "confidence": "high",
                               "evidence_span": "a limit of 96 MHz"}, FRAGMENTS)
        self.assertEqual(r["support_label"], "REVIEW")
        self.assertEqual(r["reason"], "quote_not_in_retrieved_evidence")

    def test_no_insufficiency_from_five_fragments(self):
        r = validate_judgment({"support_label": "INSUFFICIENT", "confidence": "high",
                               "evidence_span": None}, FRAGMENTS)
        self.assertEqual(r["support_label"], "REVIEW")
        self.assertEqual(r["reason"], "insufficiency_not_certified")

    def test_current_status_cannot_be_certified_by_quote_alone(self):
        r = validate_judgment({"support_label": "SUPPORTED", "confidence": "high",
                               "evidence_span": "a limit of 72 MHz"}, FRAGMENTS,
                              {"claim_scope": "current_status"})
        self.assertEqual(r["support_label"], "REVIEW")
        self.assertEqual(r["reason"], "temporal_status_not_certified")


if __name__ == "__main__":
    unittest.main()