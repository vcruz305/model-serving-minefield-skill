# Diagnostic contract

This reference preserves the separation between evidence, applicability,
diagnosis, and mechanism.

## Canonical result

Use this exact shape when structured output is requested:

```json
{
  "trap_id": "00",
  "diagnosis_level": "POSSIBLE_RELATED_TRAP",
  "evidence_status": "published status verbatim",
  "matched_conditions": [],
  "mismatched_conditions": [],
  "unknown_conditions": [],
  "direct_probe_support": false,
  "direct_probe_result": "not_supplied",
  "mechanism_status": "PROPOSED_NOT_PROVEN",
  "observed_symptom": "",
  "pattern_resemblance": "",
  "supported_mechanism": "",
  "proposed_mechanism": "",
  "unresolved_mechanism": "",
  "confirmation_check": "",
  "refutation_check": "",
  "conditional_mitigation": "",
  "remaining_unknowns": [],
  "mutation_authority_warning": ""
}
```

Do not rename keys or replace booleans with prose.

Allowed `diagnosis_level` values:

- `CONFIRMED_BY_DIRECT_PROBE`
- `STRONG_CONDITION_MATCH_REQUIRES_CONFIRMATION`
- `POSSIBLE_RELATED_TRAP`
- `CONDITION_MISMATCH`
- `NOT_APPLICABLE`
- `NOT_DOCUMENTED`
- `INCONCLUSIVE`

Recommended `direct_probe_result` values:

- `not_supplied`
- `confirmed`
- `refuted`
- `inconclusive`

Diagnosis level and mechanism status are independent. A direct probe may
confirm a narrow assertion without proving the proposed mechanism.

## L-series lead result

L-series items are deliberately non-canonical:

```json
{
  "lead_id": "L000",
  "canonical": false,
  "lead_match_level": "POSSIBLE_UNVERIFIED_LEAD",
  "evidence_status": "preserved lead status",
  "confidence": "low|medium|high",
  "pattern_resemblance": "",
  "possible_mechanism": "",
  "confirmation_check": "",
  "refutation_check": "",
  "conditional_mitigation": ""
}
```

Never call an L-series ID a trap, reproduced evidence, or a confirmed root
cause.

## Evidence discipline

Preserve the canonical entry's evidence status **verbatim**. The upstream
registry uses evidence labels to distinguish what was reproduced locally from
what was contributed or reported elsewhere.

Do not convert:

- `reported by others` -> reproduced
- `contributor-measured` -> reproduced
- `measured here, raw not published` -> independently verifiable
- `under test` -> confirmed

For contributor evidence say:

> Contributor-measured under reported conditions; not independently reproduced here.

Evidence status describes the source record. Diagnosis level describes how well
that record fits this user's incident. Neither one upgrades the other.

## Applicability rules

Compare only documented relevant conditions. Missing metadata is unknown.

Use `CONDITION_MISMATCH` for a material difference in any condition that the
trap depends on, including:

- hardware architecture or device class
- topology / node count / parallelism
- stack or build
- exact checkpoint
- quantization
- context or concurrency regime
- failure stage
- operating system when relevant

Same architecture does not imply same device class. Same model family does not
imply same checkpoint. Same quantization label does not imply same runtime
kernel path.

If every documented relevant condition is supplied and matches, and no direct
probe exists, use `STRONG_CONDITION_MATCH_REQUIRES_CONFIRMATION`.

## Causal-language boundary

Without trap-appropriate direct evidence on this system, prefer:

- "resembles"
- "is consistent with"
- "candidate"
- "possible match"
- "worth testing"

Avoid:

- "is caused by"
- "root cause"
- "this proves"
- "definitely trap X"
- "your GPU/server/model has X"

## Canonical miss

If no canonical trap applies:

```json
{
  "diagnosis_level": "NOT_DOCUMENTED"
}
```

A miss means only that the strict registry does not document the incident as a
canonical trap. It does not mean the system is safe or correctly configured.

After a canonical miss, inspect L-series possible/unverified leads separately.
