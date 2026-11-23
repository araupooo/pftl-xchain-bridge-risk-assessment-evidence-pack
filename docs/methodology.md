# Methodology

## Sources, in order of authority

1. **Pinned postfiatd source** (`0085a1ff885d6a446369cf73a4430f75af22be55`,
   local checkout `/tmp/postfiatd-pin`, HEAD verified with
   `git rev-parse HEAD`). Every cited line number was verified with
   `grep -n` on that checkout. Raw-file fetches were never used for
   line numbers.
2. **Live public RPC** (https://rpc.testnet.postfiat.org/), read-only
   methods only. Every response is saved unedited under `outputs/`
   as a `{http_status, method, params, probed_at_utc, response}`
   envelope.
3. **Public documents**: the validator list
   (https://postfiat.org/testnet_vl.json), the VHS amendments
   registry (https://vhs.testnet.postfiat.org/v1/network/amendments/info),
   the PostFiat pfUSDC page, and the upstream XRPL XChain reference
   (xrpl.org, labelled as upstream, not pinned).
4. **Lab drills** against `src/xchain_model.py`, a pure-stdlib
   mirror of the pinned rules on synthetic data.

## What was NOT done

- No transaction was submitted, no vote was cast, no signature was
  produced, no credential was used or needed.
- No bridge interaction of any kind: no bridge was created, no
  claim id was checked out, no attestation was submitted.
- No peer connection was opened to the live network.
- No Ed25519 verification was run: the Python standard library
  has no Ed25519, so `AttestationBase::verify` is modelled as an
  input (`signature_valid`) and the claim that depends on it is
  marked UNTESTABLE (C-27, G-01).

## How the live numbers were produced

`scripts/probe_all.py` (17 HTTP calls):

- 5 no-parameter RPC calls: `server_info`, `ledger_current`,
  `ledger_closed`, `fee`, `feature`.
- `account_info` (validated ledger) for the PFTL genesis account
  and for the masterpassphrase-derived root account.
- `account_objects` (validated ledger) for the genesis account.
- `ledger_entry` (validated ledger) for a fabricated bridge spec:
  locking door = genesis, locking issue = XRP, issuing door =
  masterpassphrase root, issuing issue = XRP, bridge_account =
  genesis. The expected answer for a non-existent bridge is
  `entryNotFound`; any other answer would have been recorded as-is.
- GETs: validator list, VHS amendments info, pfUSDC page, explorer
  homepage, explorer /health, explorer.postfiat.org.
- Cadence: two `ledger_current` reads 61.2 s apart (8287778 →
  8287798, 20 ledgers, 3.059 s/ledger).

`scripts/analyze.py` cross-checks the shipped outputs (24 checks)
and writes the derived tables. `scripts/drill.py` runs the 24 lab
cases. `scripts/clean_reproduce.sh` re-runs everything fresh into
`outputs/fresh-clone/` and `scripts/compare_reproduce.py` compares
the fresh run against the shipped run (15 checks; ledger numbers
must advance, invariants must hold).

## How the drills relate to the pinned code

Each drill case asserts one rule of the pinned code, re-implemented
in `src/xchain_model.py` from the cited source lines:

- Drill A mirrors `onNewAttestations` (replace, never double-count),
  `claimHelper` (erase non-signers, sum weights, `weight >= quorum`),
  and `onClaim` (destination ignored on the claim path).
- Drill B mirrors `claimHelper`'s quorum comparison at the boundary
  (quorum-1, exactly quorum, above quorum), the match rules (amount
  and chain direction must match), and `XChainCreateClaimID::doApply`
  (counter + 1, wrap to 0 → `tecINTERNAL`).
- Drill C mirrors `XChainCreateBridge::preflight` (all nine rejection
  rules, in the pinned check order) and `attestationpreflight`
  (bad key type, bad proof).

The model is a mirror, not the code: a drill passing proves the
mirror implements the rule as read, not that the C++ compiles to it.
The verbatim excerpts are the evidence for what the C++ says.

## Count discipline

Every count in this pack was recomputed from the table it
summarises. Claim status is column 2 of `docs/claim-index.md`.
Findings, risks, and gaps were counted from their own tables, and
the README totals were checked against those counts after the last
edit.
