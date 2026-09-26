#!/usr/bin/env python3
"""Open-pilot-only v0.6 hybrid wiring. The external judge is an explicit subprocess.

This development harness never loads blind claims or labels, and does not claim
an accuracy score. Model judgment is provisional until a model/prompt is frozen.
"""

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path

from uars_v06_preflight import run


PROMPT = ("You compare one claim with only the supplied archived evidence fragments. "
          "Return a JSON object with support_label SUPPORTED, CONTRADICTED, "
          "INSUFFICIENT, or REVIEW; confidence high, medium, or low; "
          "evidence_span as an exact copied substring for SUPPORTED or CONTRADICTED; "
          "and a brief reason. Never add facts from memory. A missing fact in the "
          "fragments cannot establish that it is absent from the full source: "
          "use REVIEW unless you have a documented complete-context rule.")


def review(reason, *, path="abstain", detail=None):
    out = {"support_label": "REVIEW", "source_role": "UNKNOWN",
           "evidence_span": None, "span_start": None,
           "decision_path": path, "reason": reason}
    if detail:
        out["detail"] = detail[:180]
    return out


def validate_judgment(payload, retrieved, claim=None):
    if not isinstance(payload, dict):
        return review("invalid_model_json")
    label = payload.get("support_label")
    confidence = payload.get("confidence")
    quote = payload.get("evidence_span")
    if label not in ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT", "REVIEW"):
        return review("invalid_model_label")
    if confidence not in ("high", "medium", "low"):
        return review("invalid_model_confidence")
    if label == "REVIEW" or confidence == "low":
        return review("model_abstained", path="llm_fallback")
    if claim and claim.get("claim_scope") == "current_status":
        return review("temporal_status_not_certified", path="llm_fallback")
    if label == "INSUFFICIENT":
        return review("insufficiency_not_certified", path="llm_fallback")
    if not isinstance(quote, str) or not quote.strip():
        return review("missing_exact_quote", path="llm_fallback")
    matches = [fragment for fragment in retrieved if quote in fragment["text"]]
    if not matches:
        rejected = review("quote_not_in_retrieved_evidence", path="llm_fallback")
        rejected["rejected_evidence_span"] = quote[:2000]
        rejected["rejected_quote_length"] = len(quote)
        rejected["rejected_quote_truncated"] = len(quote) > 2000
        return rejected
    chosen = min(matches, key=lambda fragment: fragment["start"])
    return {"support_label": label, "source_role": "UNKNOWN",
            "evidence_span": quote, "span_start": chosen["start"] + chosen["text"].find(quote),
            "decision_path": "llm_fallback", "confidence": confidence,
            "reason": str(payload.get("reason", ""))[:500]}


def subprocess_judge(command, claim, retrieved, timeout):
    request = {"prompt": PROMPT, "claim_id": claim["candidate_id"],
               "claim_text": claim["claim_text"], "claim_scope": claim["claim_scope"],
               "fragments": retrieved}
    try:
        result = subprocess.run(shlex.split(command), input=json.dumps(request, ensure_ascii=False),
                                capture_output=True, text=True, timeout=timeout, check=False)
        if result.returncode != 0:
            return review("model_process_failed", detail=f"exit code {result.returncode}")
        return validate_judgment(json.loads(result.stdout), retrieved, claim)
    except (OSError, ValueError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        return review("model_unavailable_or_invalid", detail=type(exc).__name__)


def evaluate(preflight, pilot, command=None, timeout=60):
    claims = {c["candidate_id"]: c for c in pilot["claims"]}
    results = []
    for row in preflight["results"]:
        cid = row["candidate_id"]
        baseline = row["development_baseline"]
        if baseline["support_label"] != "REVIEW":
            final = dict(baseline, decision_path="deterministic")
            attempted = False
        elif not command:
            final = review("llm_not_configured")
            attempted = False
        else:
            attempted = True
            final = subprocess_judge(command, claims[cid], row["top_k"], timeout)
        results.append({"candidate_id": cid,
                        "previously_disclosed": bool(claims[cid].get("previously_disclosed", False)),
                        "baseline_label": baseline["support_label"],
                        "llm_attempted": attempted,
                        "hybrid_dev": final, "scanned_windows": row["scanned_windows"]})
    return {"status": "OPEN_PILOT_DEV_ONLY", "prompt_sha256": hashlib.sha256(PROMPT.encode()).hexdigest(),
            "llm_configured": bool(command),
            "llm_attempts": sum(r["llm_attempted"] for r in results),
            "diagnostic_change_after_open_pilot": "rejected_quote_capture_v1",
            "semantic_quality_measured": False, "results": results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "archive", "pilot", "split", "precommit", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--llm-command", help="Local program receiving one JSON request on stdin and returning JSON")
    parser.add_argument("--llm-model-id", help="Exact model name to record in this development output")
    parser.add_argument("--llm-model-digest", help="Installed model digest to record in this development output")
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()
    preflight = run(args.manifest, args.archive, args.pilot, args.split, args.precommit)
    pilot = json.loads(Path(args.pilot).read_text())
    results = evaluate(preflight, pilot, args.llm_command, args.timeout)
    results["llm_model_id"] = args.llm_model_id
    results["llm_model_digest"] = args.llm_model_digest
    Path(args.output).write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print("Open pilot only;", len(results["results"]), "IDs; LLM configured:", bool(args.llm_command))
    for r in results["results"]:
        print(r["candidate_id"], r["baseline_label"], "→", r["hybrid_dev"]["support_label"],
              r["hybrid_dev"]["reason"])


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError, OSError) as exc:
        sys.exit(f"DEVELOPMENT RUN FAILED: {exc}")