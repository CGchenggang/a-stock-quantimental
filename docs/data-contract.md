# Data Contract

## Canonical record

```text
symbol
field
value
event_time
available_time
fetched_at
source
source_type
quality
raw_ref
revision
```

## Time semantics

`event_time` = fact/event happened.

`available_time` = system could know it.

Backtest eligibility:

```python
available_time <= decision_time
```

Never substitute `event_time` for `available_time`.

## Source semantics

`source_type` examples:

```text
official
exchange
vendor
news
derived
proxy
```

A derived/proxy field must not be represented as an objective fact.

## Quality

Suggested levels:

```text
A
B
C
D
INVALID
```

The exact implementation may evolve, but quality must be explicit.
