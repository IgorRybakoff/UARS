#!/usr/bin/env python3
"""Open-pilot candidate plus decisive substring experiment; no blind claims."""

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
import unicodedata
from pathlib import Path

from uars_v06_preflight import run, score, tokens_with_offsets
from uars_v06_hybrid_dev import review


PROMPT = (
    "Compare the claim only with the supplied archived evidence candidates. "
    "Return JSON with support_label SUPPORTED, CONTRADICTED, INSUFFICIENT, or REVIEW; "
    "confidence high, medium, or low; reason brief. For SUPPORTED or CONTRADICTED, "
    "set evidence_span to exactly one candidate ID such as C03, AND decisive_text to "
    "a short, contiguous, verbatim substring of THAT candidate's text which by itself "
    "establishes the asserted relation or contradiction. Preserve PDF newlines and "
    "hyphens exactly; no paraphrase. Do not select a candidate that only mentions "
    "the topic. If no single candidate and verbatim decisive_text suffice, return "
    "REVIEW with null evidence_span and null decisive_text. "
    "Do not use memory. A missing fact in these excerpts cannot establish that it is "
    "absent from the complete source: use REVIEW."
)


def candidates(claim_text, retrieved, per_fragment=3, size=65, stride=30):
    """Stable, bounded excerpts of actual retrieved text with absolute offsets."""
    out = []
    for fragment in retrieved:
        ts = tokens_with_offsets(fragment["text"])
        if not ts:
            continue
        choices = []
        for i in range(0, len(ts), stride):
            j = min(i + size, len(ts))
            start, end = ts[i][1], ts[j - 1][2]
            excerpt = fragment["text"][start:end]
            choices.append((score(claim_text, {"tokens": [t[0] for t in ts[i:j]]}),
                            start, end, excerpt))
            if j == len(ts):
                break
        for _, start, end, excerpt in sorted(choices, key=lambda x: (-x[0], x[1]))[:per_fragment]:
            absolute = fragment["start"] + start
            if any(c["start"] == absolute and c["text"] == excerpt for c in out):
                continue
            out.append({"id": f"C{len(out):02d}", "start": absolute,
                        "end": fragment["start"] + end, "text": excerpt})
    return out


def validate(payload, choices, claim):
    if not isinstance(payload, dict):
        return review("invalid_model_json")
    label, confidence, choice_id = (payload.get("support_label"), payload.get("confidence"),
                                    payload.get("evidence_span"))
    decisive = payload.get("decisive_text")
    if label not in ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT", "REVIEW"):
        return review("invalid_model_label")
    if confidence not in ("high", "medium", "low"):
        return review("invalid_model_confidence")
    if not isinstance(claim, dict) or claim.get("claim_scope") not in (
            "document_content", "current_status"):
        return review("invalid_claim_scope", path="llm_fallback")
    if label == "REVIEW" or confidence == "low":
        return review("model_abstained", path="llm_fallback")
    if claim.get("claim_scope") == "current_status":
        return review("temporal_status_not_certified", path="llm_fallback")
    if label == "INSUFFICIENT":
        return review("insufficiency_not_certified", path="llm_fallback")
    matches = [c for c in choices if c["id"] == choice_id]
    if len(matches) != 1:
        return review("invalid_evidence_candidate_id", path="llm_fallback")
    c = matches[0]
    if not isinstance(decisive, str) or not 15 <= len(decisive) <= 240:
        return review("decisive_text_not_in_selected_candidate", path="llm_fallback")
    if decisive not in c["text"]:
        if unicodedata.normalize("NFC", decisive) in unicodedata.normalize("NFC", c["text"]):
            return review("unicode_normalization_mismatch", path="llm_fallback")
        return review("decisive_text_not_in_selected_candidate", path="llm_fallback")
    offset = c["text"].find(decisive)
    if c["text"].find(decisive, offset + 1) != -1:
        return review("ambiguous_decisive_text", path="llm_fallback")
    return {"support_label": label, "source_role": "UNKNOWN", "evidence_span": decisive,
            "span_start": c["start"] + offset,
            "evidence_candidate_id": c["id"], "context_span": c["text"],
            "context_start": c["start"],
            "decision_path": "llm_fallback", "confidence": confidence,
            "reason": str(payload.get("reason", ""))[:500]}


def judge(command, claim, choices, timeout):
    request = {"prompt": PROMPT, "claim_id": claim["candidate_id"],
               "claim_text": claim["claim_text"], "claim_scope": claim["claim_scope"],
               "fragments": choices}
    try:
        result = subprocess.run(shlex.split(command), input=json.dumps(request, ensure_ascii=False),
                                capture_output=True, text=True, timeout=timeout, check=False)
        if result.returncode:
            return review("model_process_failed", detail=f"exit code {result.returncode}")
        return validate(json.loads(result.stdout), choices, claim)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return review("model_unavailable_or_invalid", detail=type(exc).__name__)


def evaluate(preflight, pilot, command, timeout):
    claims = {c["candidate_id"]: c for c in pilot["claims"]}
    results = []
    for row in preflight["results"]:
        cid = row["candidate_id"]
        baseline = row["development_baseline"]
        if baseline["support_label"] != "REVIEW":
            final, attempted, count = dict(baseline, decision_path="deterministic"), False, 0
        elif not command:
            final, attempted, count = review("llm_not_configured"), False, 0
        else:
            options = candidates(claims[cid]["claim_text"], row["top_k"])
            final, attempted, count = judge(command, claims[cid], options, timeout), True, len(options)
        results.append({"candidate_id": cid, "baseline_label": baseline["support_label"],
                        "llm_attempted": attempted, "candidate_count": count,
                        "hybrid_dev": final, "scanned_windows": row["scanned_windows"]})
    return {"status": "OPEN_PILOT_DEV_ONLY", "mechanism": "candidate_decisive_substring_v2",
            "prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(),
            "llm_configured": bool(command), "llm_attempts": sum(r["llm_attempted"] for r in results),
            "semantic_quality_measured": False, "results": results}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "archive", "pilot", "split", "precommit", "output"):
        p.add_argument("--" + name, required=True)
    p.add_argument("--llm-command")
    p.add_argument("--llm-model-id")
    p.add_argument("--llm-model-digest")
    p.add_argument("--timeout", type=int, default=60)
    args = p.parse_args()
    preflight = run(args.manifest, args.archive, args.pilot, args.split, args.precommit)
    pilot = json.loads(Path(args.pilot).read_text())
    output = evaluate(preflight, pilot, args.llm_command, args.timeout)
    output["llm_model_id"], output["llm_model_digest"] = args.llm_model_id, args.llm_model_digest
    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print("Open pilot only;", len(output["results"]), "IDs; extractive candidates")
    for row in output["results"]:
        h = row["hybrid_dev"]
        print(row["candidate_id"], row["baseline_label"], "→", h["support_label"], h["reason"])


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError, OSError) as exc:
        sys.exit(f"DEVELOPMENT RUN FAILED: {exc}")
