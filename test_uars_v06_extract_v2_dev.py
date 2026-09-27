"""Ensure a decision cannot cite a phrase outside its selected candidate."""

import unittest

from uars_v06_extract_v2_dev import validate


class DecisiveSpanBoundary(unittest.TestCase):
    def test_rfc_wrong_candidate_abstains(self):
        choices = [
            {"id": "C00", "start": 100, "text": 'MUST means an absolute requirement of the specification.'},
            {"id": "C01", "start": 300, "text": 'The key words "MUST" and "SHOULD" are interpreted as described in RFC 2119.'},
        ]
        claim = {"claim_scope": "document_content"}
        answer = {"support_label": "CONTRADICTED", "confidence": "high", "evidence_span": "C01",
                  "decisive_text": "absolute requirement of the specification", "reason": "contradiction"}
        bad = validate(answer, choices, claim)
        self.assertEqual((bad["support_label"], bad["reason"]),
                         ("REVIEW", "decisive_text_not_in_selected_candidate"))
        answer["evidence_span"] = "C00"
        good = validate(answer, choices, claim)
        self.assertEqual((good["evidence_span"], good["span_start"]),
                         ("absolute requirement of the specification", 114))
        self.assertEqual((good["context_span"], good["context_start"]),
                         (choices[0]["text"], 100))

    def test_rephrased_text_and_temporal_claim_abstain(self):
        choices = [{"id": "C00", "start": 0,
                    "text": "and prove formally that a single-layer\nMoE transformer can encode knowledge by us-\ning experts"}]
        payload = {"support_label": "SUPPORTED", "confidence": "high", "evidence_span": "C00",
                   "decisive_text": "We prove formally that a single-layer MoE transformer"}
        out = validate(payload, choices, {"claim_scope": "document_content"})
        self.assertEqual(out["reason"], "decisive_text_not_in_selected_candidate")
        payload["decisive_text"] = "prove formally that a single-layer"
        out = validate(payload, choices, {"claim_scope": "current_status"})
        self.assertEqual(out["reason"], "temporal_status_not_certified")

    def test_repeated_decisive_text_in_selected_candidate_abstains(self):
        choices = [
            {"id": "C00", "start": 100,
             "text": "encode knowledge appears here; encode knowledge appears again"},
            {"id": "C01", "start": 1000,
             "text": "MoE transformer can encode knowledge"},
        ]
        payload = {"support_label": "SUPPORTED", "confidence": "high",
                   "evidence_span": "C00", "decisive_text": "encode knowledge"}
        ambiguous = validate(payload, choices, {"claim_scope": "document_content"})
        self.assertEqual((ambiguous["support_label"], ambiguous["reason"]),
                         ("REVIEW", "ambiguous_decisive_text"))
        payload["evidence_span"] = "C01"
        unique = validate(payload, choices, {"claim_scope": "document_content"})
        self.assertEqual((unique["support_label"], unique["span_start"]),
                         ("SUPPORTED", 1020))
        self.assertEqual((unique["context_span"], unique["context_start"]),
                         (choices[1]["text"], 1000))

    def test_missing_and_unknown_claim_scope_abstain(self):
        choices = [{"id": "C00", "start": 100,
                    "text": "MoE transformer can encode knowledge"}]
        payload = {"support_label": "SUPPORTED", "confidence": "high",
                   "evidence_span": "C00", "decisive_text": "encode knowledge"}
        for claim in ({}, {"claim_scope": "future_status"}, {"claim_scope": None}):
            with self.subTest(claim=claim):
                out = validate(payload, choices, claim)
                self.assertEqual((out["support_label"], out["reason"]),
                                 ("REVIEW", "invalid_claim_scope"))
                self.assertEqual(out["decision_path"], "llm_fallback")

    def test_unicode_normalization_requires_exact_source_codepoints(self):
        choices = [{"id": "C00", "start": 40,
                    "text": "The cafe\u0301 policy is active today."}]
        payload = {"support_label": "SUPPORTED", "confidence": "high",
                   "evidence_span": "C00", "decisive_text": "café policy is active"}
        mismatch = validate(payload, choices, {"claim_scope": "document_content"})
        self.assertEqual((mismatch["support_label"], mismatch["reason"], mismatch["span_start"]),
                         ("REVIEW", "unicode_normalization_mismatch", None))
        payload["decisive_text"] = "cafe\u0301 policy is active"
        exact = validate(payload, choices, {"claim_scope": "document_content"})
        self.assertEqual((exact["support_label"], exact["span_start"]), ("SUPPORTED", 44))

    def test_repeated_unicode_quote_remains_ambiguous(self):
        choices = [{"id": "C00", "start": 5,
                    "text": "The cafe\u0301 policy is active. The cafe\u0301 policy is active."}]
        payload = {"support_label": "SUPPORTED", "confidence": "high",
                   "evidence_span": "C00", "decisive_text": "cafe\u0301 policy is active"}
        out = validate(payload, choices, {"claim_scope": "document_content"})
        self.assertEqual((out["support_label"], out["reason"]),
                         ("REVIEW", "ambiguous_decisive_text"))


if __name__ == "__main__":
    unittest.main()
