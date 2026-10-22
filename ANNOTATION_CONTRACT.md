# UARS v0.7 assisted verification contract

Scope: check a claim against one explicitly identified frozen UTF-8 document.
This is document-relative verification, not a claim of universal truth.

## Separate truth labels from system outcomes

| Field | Values | Meaning |
|---|---|---|
| support_label | SUPPORTED, CONTRADICTED, INSUFFICIENT, null | Accepted reviewer judgment; null means no accepted judgment |
| system_outcome | DECIDED, REVIEW, ERROR | Accepted review, unresolved case, or failed model process |
| proposal.support_label | SUPPORTED, CONTRADICTED | Unaccepted model suggestion with mechanically checked citation |

REVIEW is not INSUFFICIENT. Missing top-k evidence never establishes absence.
A model's high confidence is not calibrated probability or source reliability.
An attestation records the reviewer identity as supplied; there is no authentication,
cryptographic signature, or automatic verification of their expertise.

## Required evidence

All offsets are zero-based Python Unicode codepoint offsets, end exclusive, in
the exact UTF-8 decoded source. No NFC normalization or casefold offset mapping.
Each accepted positive/negative judgment requires a nonempty decisive span inside
a nonempty context span. Text is reconstructed from the hashed source, never copied
from the reviewer's JSON. Read enough context to check negation, scope, conditions,
exceptions, units and dates. Span containment alone does not prove semantic adequacy.

| Situation | Expected reviewer label |
|---|---|
| Source asserts P under the same conditions as the claim | SUPPORTED |
| Source explicitly negates P under the same conditions | CONTRADICTED |
| Claim says 100 Hz at 3.3 V; source explicitly limits 3.3 V operation to 50 Hz | CONTRADICTED |
| Source asserts P only at 5 V; claim concerns 3.3 V with no further evidence | INSUFFICIENT after full source inspection; otherwise REVIEW |
| Quote merely mentions a topic, or surrounding text is unavailable | REVIEW |
| Full source lacks information needed for the claim | INSUFFICIENT only after complete source review |
| Process fails or returns invalid JSON/quote | ERROR, support_label=null |
| Current status is inferred only from an archive | REVIEW, temporal_status_not_certified |

INSUFFICIENT attestations require a context covering the entire document. That is
an explicit reviewer declaration of complete inspection, not an automated proof of
absence. Large documents can therefore produce large reports. Current-status
certification is outside this MVP and cannot be bypassed through the review command.

## Reproducibility and evaluation boundary

Run identity hashes batch contents, source hashes, retrieval configuration,
prompt hash, mechanism version, model identity/digest, judge command and timeout.
Source hashes detect byte changes; they do not authenticate a publisher or establish
that a source is correct. Local paths and supplied source URLs are provenance metadata.
Keep confidential paths and judge credentials out of shared manifests and commands.

The supplied fixture is synthetic, exposed and development-only. It exercises
negation, conditions, support and full-document insufficiency. It is not a new
independent benchmark and contains no GR006 blind material.

Reported metrics: number of claims, accepted decision coverage, review count and
process errors. Accuracy stays null without independent reference labels.
Before autonomous deployment: fresh externally annotated data, frozen mechanism,
predeclared error thresholds, conditional accuracy, false support/contradiction,
retrieval misses and abstention breakdown are still required. No blind gate is
claimed to have passed by this assisted release.
