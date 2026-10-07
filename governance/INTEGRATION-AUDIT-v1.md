# Integration Audit Protocol v1

## Inputs
- MAIN_BASE
- AI2_BRANCH
- AI3_BRANCH

## Audit
1. Verify both branches use the approved base.
2. Compare each branch against base.
3. List added/modified/deleted/renamed files.
4. Verify WRITE_SET compliance.
5. Calculate file overlap.
6. Review semantic conflicts in APIs, signatures, schemas, configs, dependencies, data contracts and runtime assumptions.
7. Run regression/build/relevant integration tests independently.
8. Check scope creep and unrelated refactoring.
9. Decide APPROVED, CONDITIONAL or REJECTED.

## Integration
Only AI1 integrates.
Worker READY states never imply acceptance.

## Final record
AI2: PASS/FAIL
AI3: PASS/FAIL
FILE_CONFLICT: YES/NO
SEMANTIC_CONFLICT: YES/NO
REGRESSION: PASS/FAIL
SCOPE: PASS/FAIL
BUILD: PASS/FAIL
INTEGRATION: APPROVED/CONDITIONAL/REJECTED
FINAL_COMMIT:
