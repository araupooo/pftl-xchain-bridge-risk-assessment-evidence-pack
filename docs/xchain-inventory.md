# XChain Bridge Inventory (pinned source)

Pinned source: postfiatorg/postfiatd @
`0085a1ff885d6a446369cf73a4430f75af22be55`. Every line number below
was verified with `grep -n` on the pinned checkout. Verbatim
excerpts live in `fixtures/source-excerpts/`; blob SHAs in
`fixtures/source-hashes.json`.

## 1. The model (what a bridge is)

`src/xrpld/app/tx/detail/XChainBridge.cpp` lines 52-98, in the file's
own words: a bridge is "a box" holding wrapped tokens; a
locking-chain token put into the box releases one wrapped token on
the issuing chain, and returning the wrapped token releases the
locked token. A "door account" on each chain holds the locked funds
and is jointly controlled by witness servers through the ledger's
multi-signature support, with the master key disabled. Witness
servers watch one chain and attest events on the other. Claim ids
prevent attestations from being reused: a claim id is a simple
counter, destroyed once the funds move, and "once it is destroyed
it can never exist again".

## 2. Transaction types (all gated on one amendment)

`include/xrpl/protocol/detail/transactions.macro` lines 526-637.
All eight XChain transaction types carry `featureXChainBridge` as
their gating amendment:

| Code | Type | Purpose |
| --- | --- | --- |
| 41 | XChainCreateClaimID | Check out a claim id (counter + 1) on the destination chain |
| 42 | XChainCommit | Put funds into the box on the source chain |
| 43 | XChainClaim | Release funds on the destination chain once quorum is reached |
| 44 | XChainAccountCreateCommit | Fund an account-creation on the destination chain |
| 45 | XChainAddClaimAttestation | A witness attests a commit event |
| 46 | XChainAddAccountCreateAttestation | A witness attests an account-create event |
| 47 | XChainModifyBridge | Change SignatureReward / MinAccountCreateAmount |
| 48 | XChainCreateBridge | Create the bridge (both doors must submit) |

The gate itself: `src/xrpld/app/tx/detail/Transactor.h` lines
409-425 — `invokePreflight` looks up the transaction type's
amendment and returns `temDISABLED` when it is not enabled.
Amendment registration:
`include/xrpl/protocol/detail/features.macro` line 84
(`XChainBridge`, DefaultNo) and line 75
(`fixXChainRewardRounding`, DefaultNo).

## 3. Ledger entry types

`include/xrpl/protocol/detail/ledger_entries.macro`:

| Code | Type | Fields |
| --- | --- | --- |
| 0x0069 | Bridge (lines 228-240) | Account, SignatureReward, MinAccountCreateAmount (optional), XChainBridge, XChainClaimID, XChainAccountCreateCount, XChainAccountClaimCount |
| 0x0071 | XChainOwnedClaimID (lines 277-290) | Account, XChainBridge, XChainClaimID, SignatureReward, OtherChainSource, XChainClaimAttestations |
| 0x0074 | XChainOwnedCreateAccountClaimID (lines 333-345) | Account, XChainBridge, XChainAccountCreateCount, XChainCreateAccountAttestations |

Keylets: `src/libxrpl/protocol/Indexes.cpp` lines 481-515. A bridge
keylet is `indexHash(BRIDGE, door, currency)` — one bridge per door
per currency. A claim-id keylet hashes the full bridge spec
(both doors, both issues) plus the claim-id sequence number.

## 4. Bridge creation validation (XChainCreateBridge)

`XChainBridge.cpp` preflight 1374-1447, preclaim 1448-1498,
doApply 1500-1544. Preflight rejects, in order:

- equal door accounts → `temXCHAIN_EQUAL_DOOR_ACCOUNTS`
- submitter is neither door → `temXCHAIN_BRIDGE_NONDOOR_OWNER`
- locking/issuing issues not both XRP or both IOU →
  `temXCHAIN_BRIDGE_BAD_ISSUES`
- non-XRP or negative SignatureReward →
  `temXCHAIN_BRIDGE_BAD_REWARD_AMOUNT`
- bad MinAccountCreateAmount (non-XRP, zero, or on a non-XRP
  bridge) → `temXCHAIN_BRIDGE_BAD_MIN_ACCOUNT_CREATE_AMOUNT`
- XRP bridge whose issuing door is not the root account
  (derived from the seed "masterpassphrase") →
  `temXCHAIN_BRIDGE_BAD_ISSUES`
- IOU bridge whose issuing door is not the asset's issuer →
  `temXCHAIN_BRIDGE_BAD_ISSUES`
- locking door locking its own asset → `temXCHAIN_BRIDGE_BAD_ISSUES`

Preclaim rejects a duplicate bridge (`tecDUPLICATE`), a missing
IOU issuer (`tecNO_ISSUER`), a clawback-enabled issuer
(`tecNO_PERMISSION` — clawback would break the invariant that
wrapped funds are always backed by locked funds), and an
under-reserved door account (`tecINSUFFICIENT_RESERVE`).
doApply creates the Bridge object with all three counters at zero
(`sfXChainClaimID`, `sfXChainAccountCreateCount`,
`sfXChainAccountClaimCount`).

`BridgeModify` (preflight 1552-1595, preclaim 1596-1611, doApply
1612-1651) can change only SignatureReward and
MinAccountCreateAmount (or clear the latter with the
`tfClearAccountCreateAmount` flag). It cannot change the doors, the
issues, or the witness set.

## 5. Attestations and quorum

Attestation structure: `src/libxrpl/protocol/XChainAttestations.cpp`.
`AttestationBase::verify` (lines 102-106) checks the signature with
`ripple::verify(publicKey, message, signature)` — Ed25519. The
signed message binds the bridge, sending account, sending amount,
reward account, chain direction, claim id, and destination.

Witness admission: `checkAttestationPublicKey` (XChainBridge.cpp
111-175). The signer must be in the door account's SignerList;
otherwise `tecNO_PERMISSION`. The public key must then match the
signer's master key (which must not be disabled,
`lsfDisableMaster`) or the signer's RegularKey; otherwise
`tecXCHAIN_BAD_PUBLIC_KEY_ACCOUNT_PAIR`. An attestation for a
non-existent account is accepted only if the key derives to that
account.

Quorum math: `claimHelper` (XChainBridge.cpp 189-242). Attestations
from accounts no longer in the signers list are erased first. Then
each attestation that matches (amount, chain direction, and —
on the add-attestation path — destination) adds its signer's weight.
Quorum is reached when `weight >= quorum`; otherwise
`tecXCHAIN_CLAIM_NO_QUORUM`. The quorum and the weights come from
the door account's SignerList: `getSignersListAndQuorum`
(XChainBridge.cpp 771-810) reads `sfSignerQuorum` from the door's
signer-list object. There is no quorum field on the Bridge object
itself.

Replay safety: `onNewAttestations` (XChainBridge.cpp 282-344). A
new attestation from a signer that already attested REPLACES the old
one; it never adds a second entry. `onClaim` (346-366) is the claim
path and ignores the destination (`CheckDst::ignore`).

Attestation intake: `attestationpreflight` (1215-1240) rejects a
bad public-key type (`temMALFORMED`), a failed signature, a
non-positive amount, or an issue that is not the bridge's issue on
the sending chain (`temXCHAIN_BAD_PROOF`). `attestationPreclaim`
(1241-1271) rejects an attestation when the bridge does not exist
(`tecNO_ENTRY`) or the signer fails the public-key check.
`attestationDoApply` (1272-1372) runs `onNewAttestations` and, when
quorum is reached, triggers the transfer.

## 6. The claim / commit flow

- `XChainCreateClaimID` (preflight 1987-1996, preclaim 1998-2033,
  doApply 2035-2097): the claim id is the bridge counter + 1; a
  wrap to 0 returns `tecINTERNAL`. The new XChainOwnedClaimID
  object holds the owner, the bridge spec, the claim id, the
  other-chain source, the signature reward, and an empty
  attestation array.
- `XChainCommit` (preflight 1882-1896, preclaim 1898-1941, doApply
  1943-1985): moves the amount plus the signature reward from the
  sender to the door account; the fee may dip into the reserve.
- `XChainClaim` (preflight 1653-1668, preclaim 1669-1751, doApply
  1753-1868): preclaim checks the claim id exists
  (`tecXCHAIN_NO_CLAIM_ID` / `tecXCHAIN_BAD_CLAIM_ID`); doApply
  fetches the signers list and quorum and runs `onClaim` — quorum
  is checked here, not in preclaim.
- `finalizeClaimHelper` (615-760): transfers the funds to the
  destination, then distributes the reward pool equally among the
  attesting witnesses. The per-attester share divides the pool by
  the number of reward accounts; when `fixXChainRewardRounding` is
  enabled the division rounds downward, otherwise it uses the
  ambient rounding mode. If the distributed total ever exceeds the
  pool, the result is `tecINTERNAL`. The claim id is then removed
  from the owner directory and erased from the ledger (739-760).
- `XChainCreateAccountCommit` (preflight 2139-2155, preclaim
  2157-2214, doApply 2216-2263): funds an account creation on the
  destination chain; preclaim rejects a reward mismatch
  (`tecXCHAIN_REWARD_MISMATCH`), a disabled account-creation path
  (`tecXCHAIN_CREATE_ACCOUNT_DISABLED`), an insufficient create
  amount (`tecXCHAIN_INSUFF_CREATE_AMOUNT`), and a self-commit
  (`tecXCHAIN_SELF_COMMIT`); doApply increments
  `sfXChainAccountCreateCount`.

## 7. Upstream reference (labelled, not pinned)

The XChain design and transaction reference come from upstream
XRPL: xrpl.org `XChainCreateBridge` reference
(https://xrpl.org/docs/references/protocol/transactions/types/xchaincreatebridge)
— "Requires the XChainBridge amendment", one bridge per door,
SignerListSet plus master-key disable for the door accounts, and
for XRP-XRP bridges the issuing door "must be the genesis account".
The pinned postfiatd code is a fork of that design; where the two
could differ, the pinned code governs and this pack cites the
pinned code. The in-repo spec the code points to
(`docs/bridge/spec.md`, referenced in the XChainBridge.cpp header
comment) does not exist in the pinned repository.
