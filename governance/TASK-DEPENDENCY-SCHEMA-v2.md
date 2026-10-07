# Task Dependency Schema v2

> v2.2 revision (ADDITIVE): forbidden_set, zcode_agent, authorization and
> status added; pattern language, deny-wins and manifest self-exemption made
> normative. No existing field or rule below is changed. The source of truth
> for pattern semantics, contract precedence and migration is
> `governance/PARALLEL-GOVERNANCE-v2.2-ADDENDUM.md`.

Each task contract must define:

```yaml
task_id:
agent:                      # AI1 | AI2 | AI3
zcode_agent:                # executor identity; informational, no authority
base_commit:                # Task Frozen Base — see rule 10
depends_on: []
blocks: []
read_set: []
write_set: []
forbidden_set: []           # required; may be empty — see rules 6-8
shared_interfaces: []
authorization:
  human_required:           # true when the task class requires Human Authorization
  human_authorization_ref:  # pointer to the human authorization record
  ai1_authorized:           # AI1 allocation/authorization evidence
  protected_boundary_exception:  # see Always-Protected Boundary, addendum §8
acceptance:
  tests: []                 # declarative; Test Gate executes, never Scope Gate
  gates: [scope, conflict, test]
status:                     # canonical 11-state vocabulary — see rule 13
```

Rules:
1. Empty depends_on means the task is eligible after allocation.
2. A task with unmet hard dependencies cannot start.
3. Shared-interface dependencies must be explicit.
4. AI1 is the authority for dependency overrides.
5. Dependency cycles are invalid and block execution.
6. FORBIDDEN_SET is a first-class field and may be empty. The Scope Gate
   checks every changed file against it; a match FAILS the gate.
7. Deny-wins: a FORBIDDEN_SET match fails the gate even when the same file
   also matches WRITE_SET. WRITE_SET cannot override FORBIDDEN_SET.
8. Pattern language: an exact path matches exactly; `*` matches within a
   single path component and never crosses `/`; a trailing `/**` matches
   recursively. `**` in any other position is an invalid pattern and fails at
   manifest load with a schema/contract error. No negation syntax exists.
9. Manifest self-exemption: only the exact manifest path itself is exempt
   from the WRITE_SET and FORBIDDEN_SET checks. No wider pattern
   (`.agent/**`, `.agent/tasks/**`) and no other file is exempt.
10. base_commit is the Task Frozen Base and carries exactly that one
    semantic; it is not the PR base. PR-time base verification is the
    executable layer's responsibility.
11. read_set, depends_on, blocks, shared_interfaces and acceptance.tests are
    procedural fields consumed by AI1's audit process and the Test Gate; the
    Scope Gate does not enforce them.
12. When `authorization.human_required` is true,
    `authorization.human_authorization_ref` must resolve to a real record
    before the task may reach READY_TO_START. A
    `protected_boundary_exception` only lets a named path enter normal
    WRITE_SET/FORBIDDEN_SET judgment; it never bypasses deny-wins.
13. status uses the canonical 11-state vocabulary of TASK-STATE-MACHINE-v2 as
    clarified by the v2.2 addendum: no AUTHORIZED state exists and
    READY_FOR_AI1_AUDIT is a deprecated display alias of READY_FOR_AUDIT.
14. write∩forbidden language containment (v2.3 amendment; single-source
    definition: PARALLEL-GOVERNANCE-v2.2-ADDENDUM §11). A manifest FAILS at
    load when some `write_set` pattern's ENTIRE path language is subsumed by
    some `forbidden_set` pattern, per exactly the three rules quoted
    verbatim from addendum §11:

    (a) An exact write pattern that is matched by any forbidden pattern fails
        at load.
    (b) A write pattern with dir prefix `dW` (single-star or trailing `/**`
        form) fails at load against a forbidden trailing-`**` pattern
        `dF/**` iff `dW == dF` or `dW` starts with `dF + "/"`.
    (c) A write pattern `d/compW` fails at load against a forbidden pattern
        `d/compF` with the same literal directory `d` iff `compF == "*"`.

    "dir prefix", the top-level-wildcard boundary, and the partial-overlap
    legal case are defined in addendum §11.3–§11.4; consult that section for
    the authoritative definitions.

    Supersession: rule (a) subsumes and REPLACES the v2.2 exact-duplicate
    load-time check; implementations replace the v2.2 check with rule (a),
    they do not add it alongside. Implementations MUST NOT analyze
    component-level literal containment beyond rules (a)–(c) (addendum
    §11.6).
