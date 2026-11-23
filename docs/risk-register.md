# Risk Register

| ID | Severity | Risk | Evidence |
| --- | --- | --- | --- |
| R-01 | HIGH | Bridge unusable with no public activation path: XChainBridge is disabled, every XChain transaction returns temDISABLED, and the public feature RPC exposes no vote counts, so no one outside the operator can see whether activation is approaching | F-01; outputs/rpc-feature.json |
| R-02 | HIGH | XRP-XRP bridging with PFTL as issuing chain cannot operate even after enablement: the required issuing door (masterpassphrase root) does not exist on the ledger and cannot submit, hold a SignerList, or receive funds | F-02; outputs/rpc-account_info-xrpl-root.json |
| R-03 | HIGH | Witness-quorum collusion can steal locked funds (stated in the code); quorum lives in the door account's SignerList, which the door owner can change without touching the bridge object | F-03; fixtures/source-excerpts/quorum-collusion.txt |
| R-04 | MEDIUM | A bridge under an unknown door account is invisible to public queries: there is no bridge-listing RPC, and the keylet needs a door plus a currency up front | F-10; fixtures/source-excerpts/bridge-keylets.txt |
| R-05 | MEDIUM | A claim that reached quorum after a signer-list change stays dormant until a fresh attestation arrives; funds can sit locked past the point the witnesses agreed | F-06; fixtures/source-excerpts/on-new-attestation.txt |
| R-06 | MEDIUM | Without fixXChainRewardRounding the reward split uses the ambient rounding mode; over-distribution returns tecINTERNAL, so a claim that reached quorum can fail at finalize time | F-07; fixtures/source-excerpts/reward-rounding.txt |
| R-07 | MEDIUM | Claim ids never expire: a funded claim id waits indefinitely and can be executed long after the sender's intent changed | F-06; docs/xchain-inventory.md §6 |
| R-08 | MEDIUM | Two bridge designs share the "bridge" name: applying XChain committee assumptions to pfUSDC (or proof-based assumptions to XChain) misstates the trust model of both | F-08; outputs/postfiat-pfusdc-bridge.html |
| R-09 | MEDIUM | The bridge code does not enforce that a door account's master key is disabled: if it is not, the door owner can move locked funds unilaterally outside the witness quorum | F-03; docs/xchain-inventory.md §5 |
| R-10 | LOW | The in-repo bridge spec (docs/bridge/spec.md) does not exist, so implementers work from the code and upstream XRPL docs only | F-09 |
| R-11 | LOW | MinAccountCreateAmount absent means XChainAccountCreateCommit fails (per the upstream reference); the account-creation path can be silently unavailable on a bridge that otherwise works | docs/xchain-inventory.md §6; xrpl.org XChainCreateBridge reference |
| R-12 | LOW | No public vote counts for XChainBridge: activation approach is invisible from the public surface | F-10; outputs/rpc-feature.json |
| R-13 | LOW | Bridge objects are never deleted by the pinned code, so stale or abandoned bridges accumulate as ledger objects | docs/xchain-inventory.md §3 |
| R-14 | INFO | All measurements are from a testnet, not mainnet; nothing in this pack describes production behaviour | outputs/derived/probe-summary.json |
