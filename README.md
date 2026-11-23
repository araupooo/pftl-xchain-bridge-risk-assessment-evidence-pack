# PFTL XChain Bridge Risk Assessment Evidence Pack

## Verdict: CODE-COMPLETE BUT DORMANT — NO LIVE BRIDGE

The XChain machinery is complete in the pinned code: eight transaction
types gated on one amendment, weight-based witness quorum, replay-safe
attestations (one entry per signer, re-attestation replaces), claim
ids that advance 1, 2, 3 and are destroyed after the funds move, and
strict bridge-creation validation — all 24 lab drill cases pass. But
nothing can move across a bridge today. The `XChainBridge` amendment
is disabled on the live testnet, so every XChain transaction type
returns `temDISABLED`; no bridge object exists on the ledger (a
fabricated bridge lookup returns `entryNotFound`, and the genesis
account owns zero ledger objects); and the XRP issuing door the code
requires is the masterpassphrase-derived root account, which does not
exist on this network (`actNotFound`). Separately, the project's own
published bridge direction is not this committee design at all: the
pfUSDC page describes a proof-based (SP1 zkVM) bridge to Arbitrum
with no attestation committee.

- Pinned source: postfiatorg/postfiatd commit
  `0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10, PR #50 merge,
  v1.0.9)
- Live network: PFTL testnet, network ID 2025 (not XRPL mainnet)
- Probed: 2026-11-23 03:30-03:32 UTC (10:30-10:32 WIB) via
  https://rpc.testnet.postfiat.org/ — 17 HTTP calls total, all read-only
- Live at probe time: build 1.0.9, validated ledger 8287770, complete
  ledgers 8200054-8287770, 21 peers, quorum 17, cadence 3.059 s/ledger,
  validator list sequence 30 with 25 validators
- Amendments live: 101 entries, 64 enabled, 37 disabled;
  `XChainBridge` disabled, `fixXChainRewardRounding` disabled

## Counts (recomputed from their tables)

| Table | Count |
| --- | --- |
| Findings | 12 — 3 HIGH, 5 MEDIUM, 3 LOW, 1 INFO; 6 MEASURED, 6 SPECIFIED |
| Claims | 30 — 19 VERIFIED, 9 SPECIFIED, 1 UNVERIFIED, 1 UNTESTABLE |
| Risks | 14 — 3 HIGH, 6 MEDIUM, 4 LOW, 1 INFO |
| Gaps | 7 |
| Drill cases | 24/24 PASS (A 8, B 7, C 9), every case with its own elapsed time |
| Source excerpts | 29 files, line numbers verified with grep -n on the pinned checkout |

## How to reproduce

```sh
bash scripts/clean_reproduce.sh
# exit 0 only if every check passes; prints one PASS line per check.
# Re-probes the live testnet (includes a 60 s cadence window) and
# re-runs the drills from the pinned checkout.
bash scripts/verify_digests.sh   # verifies SHA256SUMS, exit 0
python3 scripts/drill.py         # lab drills only, no network access
python3 scripts/probe_all.py     # read-only live probes only
python3 scripts/analyze.py       # cross-checks shipped outputs
```

## File map

| Path | Contents |
| --- | --- |
| `README.md` | This file: verdict, counts, reproduce steps, file map |
| `docs/decision-memo.md` | Verdict and reasoning |
| `docs/xchain-inventory.md` | Source-cited inventory of every XChain mechanism |
| `docs/live-bridge-surface.md` | Live bridge-surface measurements |
| `docs/methodology.md` | How each measurement was made; boundaries |
| `docs/runbook-a.md` | Drill A: attestation replay (lab model) |
| `docs/runbook-b.md` | Drill B: quorum threshold and claim-id counter (lab model) |
| `docs/runbook-c.md` | Drill C: malformed bridge-account rejection (lab model) |
| `docs/risk-register.md` | 14 risks |
| `docs/gap-register.md` | 7 gaps |
| `docs/claim-index.md` | 30 claims with status and evidence pointer |
| `docs/citations.md` | Every pinned-source citation with file and line |
| `docs/evidence-index.md` | Every output file and what it proves |
| `docs/index.html` | Rendered results page |
| `findings.json` | 12 findings, machine-readable |
| `run-manifest.json` | Run record: versions, counts, digests |
| `configs/xchain-thresholds.json` | Every pinned constant in one place |
| `src/xchain_model.py` | Pure-stdlib model of the XChain rules |
| `scripts/` | probe_all.py, analyze.py, drill.py, extract_excerpts.py, clean_reproduce.sh, compare_reproduce.py, verify_digests.sh, make_sha256sums.sh |
| `fixtures/source-excerpts/` | 29 verbatim pinned-source excerpts |
| `fixtures/source-hashes.json` | Git blob SHA and size per excerpted file |
| `outputs/` | Unedited probe outputs, derived tables, drill-run.log, fresh-clone reproduction |

## Boundaries (read before re-running)

- Read-only probes only: no transaction submitted, no vote cast, no
  bridge interaction of any kind.
- No peer connection is ever opened to the live network. All drills
  run in the lab against `src/xchain_model.py`, a pure-stdlib mirror
  of the pinned rules, on synthetic data.
- The attestation signature check (`AttestationBase::verify`,
  Ed25519) cannot run in this pack: the Python standard library has
  no Ed25519. The model takes the signature-verification outcome as
  an input and the claim that depends on it is marked UNTESTABLE.
- The live `feature` RPC exposes no amendment vote counts, so the
  activation approach for `XChainBridge` cannot be observed from the
  public surface.
- pfUSDC (the project's proof-based bridge) lives in a different
  repository (postfiatl1v2) and is out of scope except for the
  published page the probe fetched; this pack assesses the XChain
  mechanism in pinned postfiatd.
