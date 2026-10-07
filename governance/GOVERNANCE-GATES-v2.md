# Governance Gates v2

## Scope Gate
PASS when all changed files are within WRITE_SET and no forbidden file changed.

## Conflict Gate
PASS when no unresolved file or semantic conflict exists.

## Test Gate
PASS when required tests succeed and no test was weakened/removed to obtain success.

## Integration Gate
PASS only when Scope + Conflict + Test gates pass and all required dependencies are satisfied.

## Acceptance Gate
AI1 independently validates the integrated result and records the final decision.

Gate failure stops promotion toward main.
