# Citations

Pinned source: postfiatorg/postfiatd @
`0085a1ff885d6a446369cf73a4430f75af22be55` (2026-10-10, PR #50
merge, v1.0.9). All line numbers verified with `grep -n` on the
pinned checkout. Blob SHAs in `fixtures/source-hashes.json`
(spot-checked against the GitHub API blob endpoint for
XChainBridge.cpp and transactions.macro — SHA and size agree).

## Pinned source

| # | File | Lines | What it proves |
| --- | --- | --- | --- |
| 1 | src/xrpld/app/tx/detail/XChainBridge.cpp | 52-72 | Bridge model: door accounts, witness servers, wrapped tokens |
| 2 | src/xrpld/app/tx/detail/XChainBridge.cpp | 74-77 | A quorum of witnesses that colludes can steal locked funds |
| 3 | src/xrpld/app/tx/detail/XChainBridge.cpp | 86-98 | Claim ids prevent attestation reuse; destroyed after funds move |
| 4 | src/xrpld/app/tx/detail/XChainBridge.cpp | 111-175 | checkAttestationPublicKey: signer must be in the list; key must match master or RegularKey |
| 5 | src/xrpld/app/tx/detail/XChainBridge.cpp | 189-242 | claimHelper: erase non-signers, sum weights, weight >= quorum else tecXCHAIN_CLAIM_NO_QUORUM |
| 6 | src/xrpld/app/tx/detail/XChainBridge.cpp | 282-344 | onNewAttestations: re-attestation replaces; dormant subsets need a new attestation to trigger |
| 7 | src/xrpld/app/tx/detail/XChainBridge.cpp | 346-366 | onClaim: claim path ignores the destination |
| 8 | src/xrpld/app/tx/detail/XChainBridge.cpp | 615-760 | finalizeClaimHelper: fund transfer, reward split, claim-id destruction |
| 9 | src/xrpld/app/tx/detail/XChainBridge.cpp | 675-695 | Reward split rounds downward only when fixXChainRewardRounding is enabled |
| 10 | src/xrpld/app/tx/detail/XChainBridge.cpp | 739-760 | Claim id removed from owner directory and erased after funds move |
| 11 | src/xrpld/app/tx/detail/XChainBridge.cpp | 771-810 | getSignersListAndQuorum: quorum from the door's SignerList |
| 12 | src/xrpld/app/tx/detail/XChainBridge.cpp | 1215-1240 | attestationpreflight: bad key type, bad proof |
| 13 | src/xrpld/app/tx/detail/XChainBridge.cpp | 1241-1271 | attestationPreclaim: bridge must exist; signer key check |
| 14 | src/xrpld/app/tx/detail/XChainBridge.cpp | 1272-1372 | attestationDoApply: applyClaimAttestations / applyCreateAccountAttestations |
| 15 | src/xrpld/app/tx/detail/XChainBridge.cpp | 1374-1447 | XChainCreateBridge::preflight: nine rejection rules |
| 16 | src/xrpld/app/tx/detail/XChainBridge.cpp | 1448-1498 | XChainCreateBridge::preclaim: duplicate, issuer, clawback, reserve |
| 17 | src/xrpld/app/tx/detail/XChainBridge.cpp | 1500-1544 | XChainCreateBridge::doApply: Bridge object, counters at zero |
| 18 | src/xrpld/app/tx/detail/XChainBridge.cpp | 1612-1651 | BridgeModify::doApply: only reward and min-create amount change |
| 19 | src/xrpld/app/tx/detail/XChainBridge.cpp | 1806-1830 | XChainClaim::doApply fetches signers list and quorum, runs onClaim |
| 20 | src/xrpld/app/tx/detail/XChainBridge.cpp | 1943-1985 | XChainCommit::doApply |
| 21 | src/xrpld/app/tx/detail/XChainBridge.cpp | 2035-2097 | XChainCreateClaimID::doApply: counter + 1, wrap to 0 is tecINTERNAL |
| 22 | src/xrpld/app/tx/detail/Transactor.h | 409-425 | invokePreflight: disabled gating amendment returns temDISABLED |
| 23 | src/libxrpl/protocol/XChainAttestations.cpp | 102-106 | AttestationBase::verify: ripple::verify (Ed25519) |
| 24 | src/libxrpl/protocol/Indexes.cpp | 481-515 | Bridge / claim-id / create-account keylets |
| 25 | include/xrpl/protocol/detail/transactions.macro | 526-637 | All eight XChain types gated on featureXChainBridge |
| 26 | include/xrpl/protocol/detail/features.macro | 75, 84 | fixXChainRewardRounding and XChainBridge, both DefaultNo |
| 27 | include/xrpl/protocol/detail/ledger_entries.macro | 228-240, 277-287, 333-341 | Bridge, XChainOwnedClaimID, XChainOwnedCreateAccountClaimID fields |
| 28 | src/xrpld/rpc/handlers/LedgerEntry.cpp | 120-140 | ledger_entry bridge parsing (parseBridgeFields) |

## Live sources (fetched by the probe, unedited in outputs/)

| # | Source | What it proves |
| --- | --- | --- |
| 29 | https://rpc.testnet.postfiat.org/ (`server_info`, `ledger_current`, `ledger_closed`, `fee`, `feature`) | Build 1.0.9, network 2025, validated ledger, amendment table |
| 30 | https://rpc.testnet.postfiat.org/ (`account_info`, `account_objects`, `ledger_entry`) | Genesis exists (flags 0); masterpassphrase root actNotFound; genesis owns 0 objects; fabricated bridge entryNotFound |
| 31 | https://postfiat.org/testnet_vl.json | Validator list sequence 30, 25 validators |
| 32 | https://vhs.testnet.postfiat.org/v1/network/amendments/info | Registry entries for XChainBridge and fixXChainRewardRounding (103 entries) |
| 33 | https://postfiat.org/pfusdc-trustless-bridge/ | pfUSDC proof-based bridge design, testnet round trip, audits pending |

## Upstream reference (labelled, not pinned)

| # | Source | What it proves |
| --- | --- | --- |
| 34 | https://xrpl.org/docs/references/protocol/transactions/types/xchaincreatebridge | Upstream XChainCreateBridge reference: amendment required, one bridge per door, SignerListSet + master-key disable, XRP issuing door must be the genesis account, MinAccountCreateAmount absence disables account creation |
