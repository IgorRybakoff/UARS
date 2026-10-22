# UARS: practical implementation report — 22 October 2026

## Delivered behavior

A user can now check a batch of claims against local technical-document text,
inspect retrieved context, optionally collect model proposals, and apply explicit
reviewer decisions. The output includes source identity, exact source-relative
citations, context, reasons, reviewer metadata and JSON/Markdown reports.
This is an assisted practical MVP, not a completed autonomous semantic evaluator.

## Changes

- Added `uars.py` CLI, Python standard library only.
- Added exact-byte source integrity and run configuration identity.
- Separated accepted support labels, system outcomes and model proposals.
- Added decisive/context span validation and complete-source insufficiency review.
- Prevented stale reviews, invalid offsets, input overwrites and inherited report labels.
- Removed the unsafe exact-substring automatic SUPPORTED baseline.
- Added annotation contract, run instructions, an exposed fictional R&D equipment
  fixture, a reviewed example and GitHub Actions configuration.
- Preserved GR006 blind material outside this implementation.

## Verification performed

Environment: Python 3.12.14. `python -m unittest discover -v`: **28 tests passed**
(10 existing, 18 new). `git diff --check`: passed.

The CLI was executed end to end on the fictional equipment fixture:

| Step | Claims | Accepted decisions | Pending | Errors |
|---|---:|---:|---:|---:|
| verify, no model | 4 | 0 | 4 | 0 |
| apply synthetic reference reviews | 4 | 4 | 0 | 0 |

Accepted fixture labels: one support, two contradictions (voltage condition and
wireless negation), one full-document insufficiency. These reviews are predefined
reference data. No live model was used; the subprocess tests use explicit fixture
processes to exercise transport, timeout and invalid-output behavior. The 100%
review coverage is not model accuracy. Accuracy is intentionally null.

## Practical use and remaining work

The immediate application is an analyst's R&D specification/AI-report audit with
a reviewer in the loop. Current input is pre-extracted UTF-8 text. No GUI,
built-in PDF/OCR, model adapter or independent semantic benchmark is delivered.
The declared reviewer identity is not authenticated. Large documents may require
manual context expansion beyond retrieved windows.

The highest-priority next acceptance step is one real technical document with
10–20 user-relevant claims, a connected target model and domain-reviewed outcomes.
Measure rejected proposals, retrieval misses and time saved. Autonomous acceptance
must wait for independent annotated data and predeclared error thresholds.
