# Runbook A — Attestation Replay (lab drill)

## Purpose

Prove that a second attestation from the same witness does not
double-count toward quorum, following the pinned rules in
`src/xrpld/app/tx/detail/XChainBridge.cpp`.

## Pinned rules under test

- `onNewAttestations` (lines 282-344): "an attestation from a signer
  that already attested REPLACES the old one" — the collection holds
  one entry per signer account, keyed by `attestationSignerAccount`.
- `claimHelper` (lines 189-242): attestations from accounts no
  longer in the signers list are erased first; then each matching
  attestation adds its signer's weight; quorum is reached when
  `weight >= quorum`, otherwise `tecXCHAIN_CLAIM_NO_QUORUM`.
- `onClaim` (lines 346-366): the claim path runs `claimHelper` with
  `CheckDst::ignore` — the destination is not checked.

## Setup

Lab only. `python3 scripts/drill.py` (drill A, cases A-01..A-08).
Model: `src/xchain_model.py`. Fixture: 3 witnesses with weights
2/2/1, quorum 5, attested amount 1,000,000 drops. No network access,
no live interaction, synthetic data only.

## Cases

| ID | Case | Expected |
| --- | --- | --- |
| A-01 | Single attestation, claim attempted | `tecXCHAIN_CLAIM_NO_QUORUM` (weight 0 < 5) |
| A-02 | Three distinct signers attest | Quorum; 3 reward accounts |
| A-03 | Same signer attests twice (replay, same amount) | Still 1 entry; weight 2 < 5; no quorum |
| A-04 | Same signer re-attests with a larger amount | Old attestation replaced; set stays 1; weight still 2 |
| A-05 | Attestation from a non-signer | `tecNO_PERMISSION`; entry erased before quorum math |
| A-06 | Destination mismatch | Excluded on the add-attestation path (`CheckDst::check`); ignored on the claim path (`CheckDst::ignore`) |
| A-07 | Signer removed from the signers list | Its attestation erased; weight 4 < 5; no quorum |
| A-08 | Weighted boundary | 2+2 = 4 no quorum; +1 = 5 quorum |

## Result

8/8 PASS. Every case carries its own measured `elapsed_ms` in
`outputs/derived/drill-results.json` and on its log line in
`outputs/drill-run.log`.

## Reproduce

```sh
python3 scripts/drill.py
```
