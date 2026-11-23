# Evidence Index

## Live probe outputs (unedited)

| Path | What it proves |
| --- | --- |
| `outputs/rpc-server_info.json` | Build 1.0.9, network 2025, validated ledger 8287770, complete 8200054-8287770, 21 peers, quorum 17 |
| `outputs/rpc-ledger_current.json` | Current ledger index at probe time |
| `outputs/rpc-ledger_closed.json` | Last closed ledger at probe time |
| `outputs/rpc-fee.json` | Fee levels at probe time |
| `outputs/rpc-feature.json` | 101 amendments; XChainBridge disabled; fixXChainRewardRounding disabled |
| `outputs/rpc-account_info-genesis.json` | Genesis account exists: balance 96,999,999,999,999,880 drops, flags 0, sequence 13 |
| `outputs/rpc-account_info-xrpl-root.json` | Masterpassphrase root account: actNotFound (error 19) |
| `outputs/rpc-account_objects-genesis.json` | Genesis account owns 0 ledger objects |
| `outputs/rpc-ledger_entry-bridge-genesis.json` | Fabricated bridge lookup: entryNotFound (error 98) |
| `outputs/testnet_vl.json` | Validator list document (sequence 30, 25 validators) |
| `outputs/vhs-amendments-info.json` | VHS registry: XChainBridge and fixXChainRewardRounding ids, 103 entries |
| `outputs/postfiat-pfusdc-bridge.html` | pfUSDC page, HTTP 200, 68,866 bytes, sha256 d3c0bcb7c6b751ea094a0fc59a8dccfd97fd6c5b3508072900ec1911927b1e8c |
| `outputs/probe-run.log` | Unedited probe log (17 HTTP calls, 03:30-03:32 UTC) with per-file SHA-256 |
| `outputs/derived/probe-summary.json` | Machine-readable probe summary |

## Lab drill outputs

| Path | What it proves |
| --- | --- |
| `outputs/drill-run.log` | Unedited drill log: 24/24 PASS with per-case elapsed times |
| `outputs/derived/drill-results.json` | Machine-readable drill results (24 cases, per-case elapsed_ms) |

## Derived tables

| Path | What it proves |
| --- | --- |
| `outputs/derived/xchain-inventory.json` | Machine-readable bridge inventory (8 tx types, 3 ledger entries, 2 amendments, quorum/replay/claim-id rules) |
| `outputs/derived/bridge-surface.json` | Machine-readable live surface (gate, bridges on ledger, accounts, pfUSDC direction) |
| `outputs/derived/run-checks.json` | 24/24 analysis checks PASS |

## Reproduction outputs

| Path | What it proves |
| --- | --- |
| `outputs/fresh-clone-compare.log` | Fresh-clone comparison: 15/15 checks PASS |
| `outputs/fresh-clone/` | Fresh re-probe + re-drill + re-analysis outputs |

## Source excerpts

| Path | What it proves |
| --- | --- |
| `fixtures/source-excerpts/*.txt` (29 files) | Verbatim pinned-source excerpts with file, line range, and commit |
| `fixtures/source-hashes.json` | Git blob SHA and size per excerpted source file (8 files) |
