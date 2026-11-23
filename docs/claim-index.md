# Claim-to-Evidence Index

Status is column 2. VERIFIED means measured live or in a lab drill;
SPECIFIED means stated in the pinned code; UNVERIFIED means the claim
cannot be checked from the public surface; UNTESTABLE means testing it
would require an Ed25519 implementation or an action outside the
lab-only boundary.

| ID | Status | Claim | Evidence |
| --- | --- | --- | --- |
| C-01 | VERIFIED | The live testnet node runs postfiatd 1.0.9 | outputs/rpc-server_info.json (`build_version`) |
| C-02 | VERIFIED | The live network ID is 2025 (PFTL testnet, not XRPL) | outputs/rpc-server_info.json (`network_id`) |
| C-03 | VERIFIED | Validated ledger 8287770 at probe time (2026-11-23 03:32 UTC); complete ledgers 8200054-8287770 | outputs/rpc-server_info.json; outputs/derived/probe-summary.json |
| C-04 | VERIFIED | Ledger cadence 3.059 s/ledger (20 ledgers / 61.2 s) | outputs/derived/probe-summary.json (`cadence`) |
| C-05 | VERIFIED | The XChainBridge amendment is disabled on the live network (enabled false, supported true) | outputs/rpc-feature.json |
| C-06 | VERIFIED | The fixXChainRewardRounding amendment is disabled on the live network (enabled false, supported true) | outputs/rpc-feature.json |
| C-07 | VERIFIED | The live amendment table has 101 entries: 64 enabled, 37 disabled | outputs/rpc-feature.json; outputs/derived/probe-summary.json |
| C-08 | VERIFIED | The PFTL genesis account r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA exists with balance 96,999,999,999,999,880 drops, flags 0, sequence 13 | outputs/rpc-account_info-genesis.json |
| C-09 | VERIFIED | The masterpassphrase-derived root account r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59 does not exist on the live ledger (actNotFound, error_code 19) | outputs/rpc-account_info-xrpl-root.json |
| C-10 | VERIFIED | The genesis account owns zero ledger objects | outputs/rpc-account_objects-genesis.json |
| C-11 | VERIFIED | A ledger_entry lookup for a fabricated bridge (genesis locking door, XRP issues, masterpassphrase root issuing door) returns entryNotFound (error_code 98) | outputs/rpc-ledger_entry-bridge-genesis.json |
| C-12 | VERIFIED | Validator list sequence 30, 25 validators, publisher ED3F1E0DA736FCF99BE2880A60DBD470715C0E04DD793FB862236B070571FC09E2 | outputs/testnet_vl.json; outputs/derived/probe-summary.json |
| C-13 | VERIFIED | Explorer testnet homepage and /health return HTTP 200 (SPA shell); explorer.postfiat.org closes the connection without a response | outputs/derived/probe-summary.json (`explorer`) |
| C-14 | VERIFIED | The VHS amendments registry lists XChainBridge (id C98D98EE9616ACD36E81FDEB8D41D349BF5F1B41DD64A0ABC1FE9AA5EA267E9C) and fixXChainRewardRounding (id 2BF037D90E1B676B17592A8AF55E88DB465398B4B597AE46EECEE1399AB05699), 103 entries total | outputs/vhs-amendments-info.json |
| C-15 | VERIFIED | The PostFiat pfUSDC page returns HTTP 200 (68,866 bytes) and describes a proof-based bridge with no committee, no multisig, and no signer | outputs/postfiat-pfusdc-bridge.html |
| C-16 | SPECIFIED | All eight XChain transaction types (codes 41-48) are gated on the featureXChainBridge amendment | fixtures/source-excerpts/tx-types-gate.txt (transactions.macro 526-637) |
| C-17 | SPECIFIED | A transaction whose gating amendment is not enabled returns temDISABLED at preflight | fixtures/source-excerpts/temdisabled-gate.txt (Transactor.h 409-425) |
| C-18 | SPECIFIED | Witness quorum is weight-based: quorum comes from the door account's SignerList (sfSignerQuorum); the Bridge object carries no quorum field | fixtures/source-excerpts/signers-list-quorum.txt (XChainBridge.cpp 771-810) |
| C-19 | VERIFIED | A replayed attestation from the same signer does not double-count: the set keeps one entry per signer and the weight stays 2 of quorum 5 | Drill A-03, A-04; outputs/derived/drill-results.json |
| C-20 | VERIFIED | Below-quorum weight returns tecXCHAIN_CLAIM_NO_QUORUM; weight exactly equal to quorum passes (weight >= quorum) | Drill B-01, B-02, B-03; outputs/derived/drill-results.json |
| C-21 | VERIFIED | Claim ids advance 1, 2, 3 from the bridge counter; a counter at 2^32-1 wrapping to 0 returns tecINTERNAL | Drill B-07; fixtures/source-excerpts/create-claim-id-apply.txt |
| C-22 | VERIFIED | Nine malformed bridge/attestation inputs are rejected with the exact tem codes the pinned code returns (equal doors, non-door submitter, mixed issues, bad reward, bad min-create amount, non-root issuing door, self-lock, bad key type, bad proof) | Drill C-01..C-09; outputs/derived/drill-results.json |
| C-23 | SPECIFIED | After the funds move, the claim id is removed from the owner directory and erased from the ledger, and can never be used again | fixtures/source-excerpts/finalize-claim-destroy.txt (XChainBridge.cpp 739-760) |
| C-24 | SPECIFIED | Bridge creation requires distinct doors, a door-account submitter, matching XRP/IOU issues, an XRP issuing door equal to the root account (or an IOU issuing door equal to the issuer), and a locking door that is not the issue's own account | fixtures/source-excerpts/create-bridge-preflight.txt (XChainBridge.cpp 1374-1447) |
| C-25 | SPECIFIED | Bridge creation rejects a duplicate bridge (tecDUPLICATE), a missing IOU issuer (tecNO_ISSUER), a clawback-enabled issuer (tecNO_PERMISSION), and an under-reserved door account (tecINSUFFICIENT_RESERVE) | fixtures/source-excerpts/create-bridge-preclaim.txt (XChainBridge.cpp 1448-1498) |
| C-26 | SPECIFIED | An attestation signature is verified with ripple::verify (Ed25519) over a message binding the bridge, sending account, amount, reward account, chain direction, claim id, and destination | fixtures/source-excerpts/attestation-verify.txt (XChainAttestations.cpp 102-106) |
| C-27 | UNTESTABLE | The attestation signature verification itself cannot be run in this pack: it needs Ed25519, which is not in the Python standard library | G-01; src/xchain_model.py (signature_valid is a model input) |
| C-28 | SPECIFIED | The reward pool is split equally among attesting witnesses; with fixXChainRewardRounding enabled the division rounds downward, otherwise it uses the ambient rounding mode, and over-distribution returns tecINTERNAL | fixtures/source-excerpts/reward-rounding.txt (XChainBridge.cpp 675-695) |
| C-29 | UNVERIFIED | Whether any bridge ever existed under an unknown door account: no RPC lists bridges, and the probes cover only the door pair the pinned code makes identifiable | G-02; outputs/rpc-ledger_entry-bridge-genesis.json |
| C-30 | SPECIFIED | pfUSDC is a separate proof-based design in the postfiatl1v2 repository, not the XChain committee mechanism in pinned postfiatd | outputs/postfiat-pfusdc-bridge.html; docs/live-bridge-surface.md |
