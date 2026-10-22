# UARS document verification

Run: `67ed03f6734c3bffdda94cf1a7bd5fea672e6b8cd6e9a122b66bab635c699595`

Human attestations are recorded judgments; model proposals require review.
Engineering checks do not measure semantic accuracy.

## RND-001

At 5 V the sensor supports a sampling rate of 100 Hz.

Outcome: DECIDED; label: SUPPORTED

Reason: The rate and voltage condition agree.

Source: urn:uars:fictional:DemoSensor-R1
SHA-256: `e544e9555b3dc9c79ee1d49333b6bfb690e49cbcf44e956088cbb58cf1b15e21`

decisive_span [103:174]:

> The sensor supports a sampling rate of 100 Hz only when powered at 5 V.

context_span [0:273]:

> UARS demonstration fixture — fictional equipment, not a real product datasheet.
> Device: DemoSensor R1.
> The sensor supports a sampling rate of 100 Hz only when powered at 5 V.
> At 3.3 V, the maximum sampling rate is 50 Hz.
> The sensor does not support wireless communication.

Reviewer: Synthetic reference fixture; not independent human evaluation

## RND-002

At 3.3 V the sensor supports a sampling rate of 100 Hz.

Outcome: DECIDED; label: CONTRADICTED

Reason: The document limits the rate to 50 Hz at 3.3 V.

Source: urn:uars:fictional:DemoSensor-R1
SHA-256: `e544e9555b3dc9c79ee1d49333b6bfb690e49cbcf44e956088cbb58cf1b15e21`

decisive_span [175:220]:

> At 3.3 V, the maximum sampling rate is 50 Hz.

context_span [0:273]:

> UARS demonstration fixture — fictional equipment, not a real product datasheet.
> Device: DemoSensor R1.
> The sensor supports a sampling rate of 100 Hz only when powered at 5 V.
> At 3.3 V, the maximum sampling rate is 50 Hz.
> The sensor does not support wireless communication.

Reviewer: Synthetic reference fixture; not independent human evaluation

## RND-003

The sensor supports wireless communication.

Outcome: DECIDED; label: CONTRADICTED

Reason: The document explicitly excludes wireless support.

Source: urn:uars:fictional:DemoSensor-R1
SHA-256: `e544e9555b3dc9c79ee1d49333b6bfb690e49cbcf44e956088cbb58cf1b15e21`

decisive_span [221:272]:

> The sensor does not support wireless communication.

context_span [0:273]:

> UARS demonstration fixture — fictional equipment, not a real product datasheet.
> Device: DemoSensor R1.
> The sensor supports a sampling rate of 100 Hz only when powered at 5 V.
> At 3.3 V, the maximum sampling rate is 50 Hz.
> The sensor does not support wireless communication.

Reviewer: Synthetic reference fixture; not independent human evaluation

## RND-004

The sensor weighs 10 grams.

Outcome: DECIDED; label: INSUFFICIENT

Reason: No mass is specified anywhere in this complete short fixture.

Source: urn:uars:fictional:DemoSensor-R1
SHA-256: `e544e9555b3dc9c79ee1d49333b6bfb690e49cbcf44e956088cbb58cf1b15e21`

context_span [0:273]:

> UARS demonstration fixture — fictional equipment, not a real product datasheet.
> Device: DemoSensor R1.
> The sensor supports a sampling rate of 100 Hz only when powered at 5 V.
> At 3.3 V, the maximum sampling rate is 50 Hz.
> The sensor does not support wireless communication.

Reviewer: Synthetic reference fixture; not independent human evaluation

## Metrics

```json
{
  "claims": 4,
  "decided": 4,
  "decision_coverage": 1.0,
  "review": 0,
  "errors": 0,
  "accuracy": null,
  "accuracy_reason": "no independent ground truth"
}
```
