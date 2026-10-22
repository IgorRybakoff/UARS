# UARS roadmap

## Delivered: v0.7 assisted practical MVP

- Arbitrary local UTF-8 source + batch of claims; no GR006 pilot size constraint.
- SHA-256 integrity, full-text lexical retrieval, reproducible run identity.
- Optional subprocess judge; mechanically validated, unaccepted proposals.
- Separate support_label and system_outcome.
- Reviewer attestations with decisive_span and context_span reconstructed from source.
- Complete-document review requirement for INSUFFICIENT.
- JSON + Markdown report and synthetic end-to-end example.
- Removed automatic support from literal substring matching in the v0.6 baseline.

## Next practical acceptance gate

Run a real user-selected technical document with 10–20 claims, including
conditions, negations and missing information. Connect the intended local model
through the documented adapter contract. Have a domain reviewer inspect every
proposed span and decision. Record review time, rejected proposals, retrieval
misses and errors. This is a deployment pilot, not a blind accuracy claim.

## Autonomous / benchmark gate remains open

1. Fresh open development set outside the exposed pilot and blind pool.
2. Independent annotations under ANNOTATION_CONTRACT.md, resolved disagreements.
3. Predeclared thresholds for false support/contradiction and decision coverage;
   conditional accuracy, quote quality, abstention reasons and retrieval misses.
4. Freeze source bytes, model/digest, prompt, retrieval and policy before prediction.
5. Only then evaluate the unopened 62 blind GR006 IDs under a separate protocol.

Assisted release completion does not establish autonomous semantic reliability.
Any mechanism tuned after evaluation makes that evaluation development-only.
