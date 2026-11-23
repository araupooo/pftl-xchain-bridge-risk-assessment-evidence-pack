# Runbook B — Quorum Threshold and Claim-ID Counter (lab drill)

## Purpose

Prove that below-threshold witness weight cannot authorise a claim,
and that claim ids advance as a guarded counter, following the
pinned rules in `src/xrpld/app/tx/detail/XChainBridge.cpp`.

## Pinned rules under test

- `claimHelper` (lines 189-242): only attestations matching the
  claimed amount and chain direction count; `weight >= quorum` is
  the whole test; anything less returns
  `tecXCHAIN_CLAIM_NO_QUORUM`.
- `XChainCreateClaimID::doApply` (lines 2035-2097): the claim id is
  the bridge counter + 1; a wrap to 0 returns `tecINTERNAL`.
- `finalizeClaimHelper` (lines 739-760): after the funds move, the
  claim id is removed from the owner directory and erased from the
  ledger — it can never be used again.

## Setup

Lab only. `python3 scripts/drill.py` (drill B, cases B-01..B-07).
Model: `src/xchain_model.py`. Fixture: 3 witnesses with weights
2/2/1, quorum 5, attested amount 1,000,000 drops. No network access,
no live interaction, synthetic data only.

## Cases

| ID | Case | Expected |
| --- | --- | --- |
| B-01 | Empty attestation set | `tecXCHAIN_CLAIM_NO_QUORUM` |
| B-02 | Weight 4 = quorum − 1 | `tecXCHAIN_CLAIM_NO_QUORUM` |
| B-03 | Weight exactly 5 = quorum | Quorum (`weight >= quorum`) |
| B-04 | Weight 9 > quorum | Quorum; reward accounts = the 3 attesters |
| B-05 | Claim amount 2,000,000 vs attestations for 1,000,000 | No match → `tecXCHAIN_CLAIM_NO_QUORUM` |
| B-06 | Locking-send attestations vs issuing-send claim | No match → `tecXCHAIN_CLAIM_NO_QUORUM` |
| B-07 | Claim-id counter 0 → 1 → 2 → 3; counter at 2^32 − 1 | Next id is 0 → `tecINTERNAL` |

## Result

7/7 PASS. Every case carries its own measured `elapsed_ms` in
`outputs/derived/drill-results.json` and on its log line in
`outputs/drill-run.log`.

## Reproduce

```sh
python3 scripts/drill.py
```
