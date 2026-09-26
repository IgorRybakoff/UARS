# UARS

**UARS — evidence-first verification framework for AI-assisted decisions.**

Public status: **v0.6 development prototype**. This repository is intentionally conservative: it distinguishes engineering checks from semantic quality claims and does not present development-pilot results as blind accuracy.

## Current architecture

```text
Claim + frozen evidence
        ↓
Evidence integrity / preflight
        ↓
Full-text retrieval
        ↓
Deterministic exact-match baseline
        ↓
Optional semantic judge subprocess
        ↓
Quote / offset validation
        ↓
SUPPORTED / CONTRADICTED / REVIEW
```

## Core principles

- Evidence is checked against frozen hashes before evaluation.
- Blind IDs must not enter development preflight.
- Retrieval covers the full normalized text, not just the first chunks.
- A semantic judge cannot invent evidence: accepted positive/negative judgments require an exact quote present in retrieved evidence.
- Top-k silence is **not** treated as proof of insufficiency.
- `current_status` claims fail closed unless temporal validity is independently certified.
- Development results are not reported as accuracy unless ground truth and evaluation protocol are frozen in advance.

## What is implemented

- `uars_v06_preflight.py` — archive/hash/split validation, full-text windowing and conservative exact-match baseline.
- `uars_v06_hybrid_dev.py` — optional external semantic judge over a subprocess JSON contract with exact-quote validation and abstention rules.
- `test_uars_v06_preflight.py` — preflight safety checks.
- `test_uars_v06_hybrid_dev.py` — quote, abstention and temporal-boundary checks.

The current code uses the Python standard library only.

## Current evidence

The open GR006 development pilot used 8 exposed IDs. The integrity run verified all 8 raw and normalized evidence artifacts against their recorded hashes and read **0 blind IDs**. The development harness produced two deterministic exact-substring `SUPPORTED` cases and abstained on the remaining cases when no semantic model was configured.

After connecting a local Qwen development judge, the mechanism was iterated on the already-exposed pilot. That work is useful for diagnostics only. It is **not** an independent evaluation. The current audit explicitly concludes that freeze and blind evaluation are premature.

## Current boundary

The main unresolved issue is not transport or hashing. It is semantic sufficiency: an exact substring may exist and still be insufficient to establish the claim. Before any blind evaluation, UARS needs:

1. a frozen annotation contract;
2. a fresh open development set outside the existing blind pool;
3. predeclared metrics separating coverage, conditional accuracy, false support/contradiction, quote quality and abstention reasons;
4. an audit of decisive span **plus context span**;
5. a frozen model/prompt/retrieval/policy configuration.

## Repository scope

This public repository contains the executable development mechanism and safety tests. Blind GR006 claims/labels are intentionally not published here.

## Research stance

UARS is designed around one rule: **do not convert uncertainty into a confident answer merely because an LLM can produce one.**

Status: active research / development prototype.