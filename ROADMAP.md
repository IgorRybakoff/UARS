# UARS roadmap

## Next gate

Before any blind evaluation:

1. Freeze a single annotation contract mapping `support_label` and system abstention reasons.
2. Separate `support_label` from `system_outcome` so abstention is not silently counted as `INSUFFICIENT`.
3. Require both `decisive_span` and `context_span` for positive/negative semantic judgments.
4. Predeclare metrics: decision coverage, conditional accuracy on decided cases, false support/contradiction, quote quality, abstention reasons, retrieval misses.
5. Build a fresh open development set outside the existing GR006 blind pool.
6. Freeze claim text, scope, source URL, raw/norm bytes, SHA-256, retrieval settings, model/digest, prompt and abstention policy before prediction.
7. Run the new open set once, preserve full JSON and hashes, and treat any subsequent tuning on it as development-only.

## Blind gate

The 62 blind GR006 IDs remain unopened until:

- source/split integrity is verified;
- nonexistent quotes and invalid offsets are mechanically rejected;
- semantic sufficiency is audited on fresh open data;
- metrics and quality thresholds are fixed in advance;
- the mechanism version is frozen.

If the mechanism changes after an evaluation, that result remains development evidence and cannot be reclassified as a blind result.