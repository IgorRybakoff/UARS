# Known limitations

UARS v0.6 is a development prototype, not a production evaluator.

## Current limitations

1. **Semantic sufficiency is not solved by exact quote matching.** A quote may be verbatim and still fail to establish the claim without surrounding context.
2. **Top-k retrieval is not proof of document silence.** Missing evidence in retrieved fragments cannot by itself justify `INSUFFICIENT`.
3. **Temporal claims require separate certification.** Archived evidence cannot automatically establish a changing `current_status` claim at a later date.
4. **The existing open GR006 pilot is exposed.** It has been repeatedly inspected during development and cannot be used as an independent evaluation set.
5. **Blind evaluation is intentionally deferred.** The 62 blind IDs remain outside development use until the annotation contract, metrics and mechanism are frozen.
6. **Source-role classification is incomplete.** Current development outputs may retain `source_role=UNKNOWN`.
7. **Model judgments are provisional.** A semantic judge is accepted only through the subprocess contract and exact-quote validation; model/prompt/retrieval/policy must be frozen before quality claims.
8. **Current local tests validate engineering boundaries, not model accuracy.**

The repository therefore reports abstention and development diagnostics explicitly instead of converting uncertainty into positive claims.