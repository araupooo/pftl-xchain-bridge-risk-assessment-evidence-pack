# Runbook C — Malformed Bridge-Account Rejection (lab drill)

## Purpose

Prove that the bridge-creation preflight and the attestation
preflight reject malformed inputs with the exact codes the pinned
code returns, following `src/xrpld/app/tx/detail/XChainBridge.cpp`.

## Pinned rules under test

- `XChainCreateBridge::preflight` (lines 1374-1447), in the pinned
  check order: equal doors → non-door submitter → mixed XRP/IOU
  issues → bad signature reward → bad min-account-create amount →
  XRP issuing door not the root account → IOU issuing door not the
  issuer → locking door locking its own asset.
- `attestationpreflight` (lines 1215-1240): bad public-key type →
  `temMALFORMED`; failed signature, non-positive amount, or wrong
  issue → `temXCHAIN_BAD_PROOF`.

## Setup

Lab only. `python3 scripts/drill.py` (drill C, cases C-01..C-09).
Model: `src/xchain_model.py`. Fixture: locking door
`rLockDoor`, XRP issuing door = the masterpassphrase root account
`r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59`. No network access, no live
interaction, synthetic data only.

## Cases

| ID | Case | Expected |
| --- | --- | --- |
| C-01 | Equal door accounts | `temXCHAIN_EQUAL_DOOR_ACCOUNTS` |
| C-02 | Submitter is neither door | `temXCHAIN_BRIDGE_NONDOOR_OWNER` |
| C-03 | Locking XRP vs issuing IOU | `temXCHAIN_BRIDGE_BAD_ISSUES` |
| C-04 | Negative reward; non-XRP reward | `temXCHAIN_BRIDGE_BAD_REWARD_AMOUNT` |
| C-05 | Non-XRP min-account-create; zero min-account-create | `temXCHAIN_BRIDGE_BAD_MIN_ACCOUNT_CREATE_AMOUNT` |
| C-06 | XRP issuing door is not the root account | `temXCHAIN_BRIDGE_BAD_ISSUES` |
| C-07 | Locking door locking its own asset | `temXCHAIN_BRIDGE_BAD_ISSUES` |
| C-08 | Attestation with unknown public-key type | `temMALFORMED` |
| C-09 | Attestation with zero amount; wrong issue; bad signature | `temXCHAIN_BAD_PROOF` |

## Result

9/9 PASS. Every case carries its own measured `elapsed_ms` in
`outputs/derived/drill-results.json` and on its log line in
`outputs/drill-run.log`.

## Reproduce

```sh
python3 scripts/drill.py
```
