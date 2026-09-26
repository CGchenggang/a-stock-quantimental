# Decision Contract

The research system should separate:

1. facts;
2. quantitative outputs;
3. AI interpretation;
4. supporting evidence;
5. contradictory evidence;
6. missing evidence;
7. risks;
8. invalidation conditions.

Decision class is a system state, not a guarantee.

Suggested values:

```text
RESEARCH
PAPER_TEST
NO_ACTION
```

The Agent may explain the result but must not silently modify quantitative outputs.
