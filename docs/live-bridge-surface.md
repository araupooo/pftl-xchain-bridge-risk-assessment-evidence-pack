# Live Bridge Surface

Probed 2026-11-23 03:30-03:32 UTC (10:30-10:32 WIB) via
https://rpc.testnet.postfiat.org/. 17 HTTP calls, all read-only.
Unedited outputs in `outputs/`; summary in
`outputs/derived/probe-summary.json`.

## Network context

| Field | Value |
| --- | --- |
| Build | 1.0.9 |
| Network ID | 2025 (PFTL testnet) |
| Validated ledger | 8287770 (age 3 s at probe time) |
| Complete ledgers | 8200054-8287770 |
| Cadence | 3.059 s/ledger (20 ledgers / 61.2 s) |
| Peers | 21 |
| Validation quorum | 17 |
| Load factor | 1 |
| I/O latency | 1 ms |
| Peer disconnects | 103 |
| Server state | full |
| Host | MUFF |
| Validator list | sequence 30, 25 validators, publisher ED3F1E0DA736FCF99BE2880A60DBD470715C0E04DD793FB862236B070571FC09E2 |

## The amendment gate (measured)

`feature` RPC: 101 entries, 64 enabled, 37 disabled
(`outputs/rpc-feature.json`).

| Amendment | Enabled | Supported |
| --- | --- | --- |
| XChainBridge | false | true |
| fixXChainRewardRounding | false | true |

The VHS registry (`outputs/vhs-amendments-info.json`, 103 entries)
lists both amendments by id — XChainBridge
`C98D98EE9616ACD36E81FDEB8D41D349BF5F1B41DD64A0ABC1FE9AA5EA267E9C`,
fixXChainRewardRounding
`2BF037D90E1B676B17592A8AF55E88DB465398B4B597AE46EECEE1399AB05699` —
with no vote data in that endpoint.

## The two candidate door accounts (measured)

| Account | Result |
| --- | --- |
| PFTL genesis `r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA` | Exists. Balance 96,999,999,999,999,880 drops (96,999,999,999.99988). Flags 0 — master key NOT disabled. Sequence 13. Ledger 8287774. (`outputs/rpc-account_info-genesis.json`) |
| Masterpassphrase root `r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59` | `actNotFound`, error_code 19, ledger 8287774. The account the pinned preflight requires as the XRP issuing door does not exist. (`outputs/rpc-account_info-xrpl-root.json`) |

## Bridge objects on the ledger (measured)

- `account_objects` on the genesis account: **0 objects**
  (ledger 8287774). The genesis account owns no Bridge, no
  XChainOwnedClaimID, and no XChainOwnedCreateAccountClaimID object.
  (`outputs/rpc-account_objects-genesis.json`)
- `ledger_entry` for a fabricated bridge (locking door = genesis,
  locking issue XRP, issuing door = masterpassphrase root, issuing
  issue XRP, bridge_account = genesis): **`entryNotFound`**,
  error_code 98. (`outputs/rpc-ledger_entry-bridge-genesis.json`)

No bridge object exists for the only plausible XRP-XRP door pair on
this network, and the genesis account owns nothing at all.

## The project's published bridge direction (measured)

`GET https://postfiat.org/pfusdc-trustless-bridge/` → HTTP 200,
68,866 bytes, sha256
`d3c0bcb7c6b751ea094a0fc59a8dccfd97fd6c5b3508072900ec1911927b1e8c`
(`outputs/postfiat-pfusdc-bridge.html`). The page describes pfUSDC,
a proof-based bridge: USDC is deposited in a vault on Arbitrum, an
SP1 zkVM proof of the exact deposit is verified on-chain against a
pinned checkpoint, and exactly the deposited amount of pfUSDC is
minted — "No committee, no multisig, no signer." Withdrawal proves
a finalized PFTL burn (including ML-DSA validator signatures
verified inside the zkVM) back to the Arbitrum vault. A complete
round trip was run on testnet against Arbitrum Sepolia; the
withdrawal released exactly 1.000000 USDC (transaction
`0x664b2897…e702c1f9`) and the proof's nullifier was consumed. The
code lives in postfiatl1v2 (vault, finality verifier, ingress/egress
guests, ML-DSA acceleration, PFTL proof verifier). The page's own
"Honest boundaries" section says this is a testnet prototype, not a
production mainnet deployment, and lists third-party audits of the
contracts and zkVM programs as remaining work.

## What is NOT observable from the public surface

- Amendment vote counts: the public `feature` RPC returns only
  name / enabled / supported. No vote totals, so the activation
  approach for `XChainBridge` cannot be seen.
- Any bridge under an unknown door account: the bridge keylet is
  `indexHash(BRIDGE, door, currency)`, and there is no RPC method
  that lists bridges. The negative probes above cover the only
  door pair the pinned code makes identifiable (genesis +
  masterpassphrase root over XRP); a bridge with an arbitrary IOU
  issuer as its door would not be found by these probes. That is
  recorded as a gap (G-02), not as proof of absence in general —
  though no code path in the pinned XChain implementation deletes
  a Bridge entry (the only erase in XChainBridge.cpp removes
  claim-id objects), so a bridge created at any point would still
  be present, and the genesis account owning zero objects bounds
  the XRP case.
- The live node's door-account configuration, signer lists, and
  witness identities: none of these exist on the ledger today
  because no bridge exists.

## Explorer

- `https://explorer.testnet.postfiat.org/` → HTTP 200 (SPA shell)
- `https://explorer.testnet.postfiat.org/health` → HTTP 200 (SPA shell)
- `https://explorer.postfiat.org/` → connection closed without response
