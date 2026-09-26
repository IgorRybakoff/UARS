#!/usr/bin/env python3
"""GR006 development preflight: evidence integrity and full-text retrieval.

No GT labels or blind claims are loaded; this is not a UARS v0.6 evaluator.
Run with only the eight open pilot IDs. Python standard library only.
"""

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def tokens_with_offsets(text):
    """Unicode word tokens; CJK ideographs are individual lexical units."""
    pattern = re.compile(r"[\u3400-\u9fff\u3040-\u30ff]|[^\W\d_]+|\d+(?:[.,]\d+)*", re.UNICODE)
    return [(m.group().casefold(), m.start(), m.end()) for m in pattern.finditer(text)]


def windows(text, size=200, overlap=50):
    if not 0 <= overlap < size:
        raise ValueError("Require 0 <= overlap < window size")
    ts = tokens_with_offsets(text)
    if not ts:
        return [{"start": 0, "end": len(text), "text": text, "tokens": []}] if text else []
    result = []
    for start in range(0, len(ts), size - overlap):
        end = min(len(ts), start + size)
        a, b = ts[start][1], ts[end - 1][2]
        result.append({"start": a, "end": b, "text": text[a:b],
                       "tokens": [t[0] for t in ts[start:end]]})
        if end == len(ts):
            break
    result[0]["start"] = 0
    result[0]["text"] = text[:result[0]["end"]]
    result[-1]["end"] = len(text)
    result[-1]["text"] = text[result[-1]["start"]:]
    if (result[0]["start"] != 0 or result[-1]["end"] != len(text)
            or any(nxt["start"] > prev["end"] for prev, nxt in zip(result, result[1:]))):
        raise RuntimeError("Full-text retrieval windows leave an uncovered region")
    return result


def score(query, fragment):
    q = set(t[0] for t in tokens_with_offsets(query))
    f = set(fragment["tokens"])
    return len(q & f) / len(q) if q else 0.0


def top_k(query, fragments, k=5):
    return [dict(start=w["start"], end=w["end"],
                 score=round(score(query, w), 6), text=w["text"])
            for w in sorted(fragments, key=lambda w: (-score(query, w), w["start"]))[:k]]


def conservative_baseline(claim_text, full_text):
    """One safe rule; semantic labels require a separately specified mechanism."""
    index = full_text.casefold().find(claim_text.casefold())
    if index >= 0 and claim_text.strip():
        return {"support_label": "SUPPORTED", "source_role": "UNKNOWN",
                "evidence_span": full_text[index:index + len(claim_text)],
                "span_start": index, "reason": "exact_claim_substring"}
    return {"support_label": "REVIEW", "source_role": "UNKNOWN",
            "evidence_span": None, "span_start": None,
            "reason": "semantic_relation_not_established_by_exact_match_baseline"}


def unique_artifact(archive, candidate_id, suffix, *roots):
    paths = [n for n in archive.namelist()
             if n.endswith("/" + candidate_id + suffix)
             and any(n.startswith(root + "/") for root in roots)]
    if len(paths) != 1:
        raise ValueError(f"{candidate_id}: expected exactly one {suffix} artifact, found {paths}")
    return archive.read(paths[0])


def run(manifest_file, archive_file, pilot_file, split_file, precommit_file,
        size=200, overlap=50, k=5):
    precommit_lines = Path(precommit_file).read_text().splitlines()
    expected = [line.split()[0] for line in precommit_lines
                if len(line.split()) == 2 and line.split()[1] == Path(split_file).name]
    if len(expected) != 1 or expected[0] != hashlib.sha256(Path(split_file).read_bytes()).hexdigest():
        raise ValueError("Split file differs from its precommit SHA-256")
    manifest_bytes = Path(manifest_file).read_bytes()
    manifest = json.loads(manifest_bytes)
    pilot = json.loads(Path(pilot_file).read_bytes())
    split = json.loads(Path(split_file).read_bytes())
    if len(pilot["claims"]) != 8 or len(split["pilot_ids"]) != 8:
        raise ValueError("Pilot must have exactly eight open IDs")
    if pilot["source_manifest_sha256"] != hashlib.sha256(manifest_bytes).hexdigest():
        raise ValueError("Pilot references a different GR006 manifest")
    ids = [c["candidate_id"] for c in pilot["claims"]]
    if len(set(ids)) != 8 or set(ids) != set(split["pilot_ids"]):
        raise ValueError("Pilot IDs do not match preregistered open split")
    if set(ids) & set(split["blind_ids"]):
        raise ValueError("A blind ID entered the development preflight")
    entries = {e["candidate_id"]: e for e in manifest["entries"]}
    output = {"status": "DEVELOPMENT_PREFLIGHT_ONLY", "manifest_sha256": sha(manifest_bytes),
              "archive_sha256": sha(Path(archive_file).read_bytes()),
              "pilot_ids": ids, "window_size": size, "overlap": overlap, "k": k,
              "results": []}
    with zipfile.ZipFile(archive_file) as archive:
        for claim in pilot["claims"]:
            cid = claim["candidate_id"]
            e = entries[cid]
            raw = unique_artifact(archive, cid, ".pdf" if e["pdf"] else ".html",
                                  "evidence_raw_gr006", "evidence_raw_gr006_supplement")
            body = unique_artifact(archive, cid, ".txt",
                                   "evidence_norm_gr006", "evidence_norm_gr006_supplement")
            if sha(raw) != e["content_hash_raw"] or sha(body) != e["content_hash_text"]:
                raise ValueError(f"{cid}: archive bytes do not match manifest")
            if claim["evidence_raw_sha256"] != sha(raw) or claim["evidence_text_sha256"] != sha(body):
                raise ValueError(f"{cid}: claim evidence hashes differ from archived bytes")
            if claim["source_url"] != e["source_url"]:
                raise ValueError(f"{cid}: source URL mismatch")
            text = body.decode("utf-8", "strict")
            fragments = windows(text, size, overlap)
            coverage_complete = bool(fragments and fragments[0]["start"] == 0
                                     and fragments[-1]["end"] == len(text)
                                     and all(nxt["start"] <= prev["end"]
                                             for prev, nxt in zip(fragments, fragments[1:])))
            if not coverage_complete:
                raise RuntimeError(f"{cid}: norm text was not fully covered by retrieval")
            candidates = top_k(claim["claim_text"], fragments, k)
            output["results"].append({"candidate_id": cid,
                                      "previously_disclosed": bool(claim.get("previously_disclosed", False)),
                                      "raw_verified": True,
                                      "norm_verified": True, "norm_chars": len(text),
                                      "scanned_windows": len(fragments),
                                      "coverage_complete": coverage_complete,
                                      "first_window_start": fragments[0]["start"] if fragments else None,
                                      "last_window_end": fragments[-1]["end"] if fragments else None,
                                      "last_token_end": tokens_with_offsets(text)[-1][2] if fragments else None,
                                      "top_k": candidates,
                                      "development_baseline": conservative_baseline(claim["claim_text"], text)})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--archive", required=True)
    parser.add_argument("--pilot", required=True)
    parser.add_argument("--split", required=True)
    parser.add_argument("--precommit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.manifest, args.archive, args.pilot, args.split, args.precommit)
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"Verified {len(result['results'])} open pilot IDs; 0 blind ID read; ")
    print("scanned windows:", [(r["candidate_id"], r["scanned_windows"]) for r in result["results"]])


if __name__ == "__main__":
    try:
        main()
    except (KeyError, ValueError, RuntimeError, OSError, zipfile.BadZipFile) as exc:
        sys.exit(f"PRECHECK FAILED: {exc}")