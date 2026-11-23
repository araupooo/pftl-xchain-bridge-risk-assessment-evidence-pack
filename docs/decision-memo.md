# Decision Memo

## Verdict: CODE-COMPLETE BUT DORMANT — NO LIVE BRIDGE

## What was assessed

The XChain cross-chain bridge mechanism in pinned postfiatd
(`0085a1ff`, v1.0.9): the eight XChain transaction types, the three
XChain ledger entry types, the witness attestation and quorum rules,
the claim-id lifecycle, and the live state of all of it on the PFTL
testnet (network 2025), probed read-only on 2026-11-23 03:30-03:32 UTC.

## Why this verdict

Three independent facts, each measured live, each sufficient on its
own to stop value from moving:

1. **The gate is off.** The `XChainBridge` amendment is disabled on
   the live testnet (`feature` RPC: enabled false, supported true;
   64 of 101 amendments enabled). All eight XChain transaction
   types carry `featureXChainBridge` as their gating amendment
   (`transactions.macro` lines 526-637), and the transactor
   preflight returns `temDISABLED` for any transaction whose gating
   amendment is not enabled (`Transactor.h` lines 409-425). No
   XChain transaction can execute on this network today.
2. **No bridge exists.** A `ledger_entry` lookup for a bridge
   between the PFTL genesis account (locking door) and the
   masterpassphrase root account (issuing door) over XRP returns
   `entryNotFound` (error 98). The genesis account owns zero ledger
   objects (`account_objects` count 0), so it owns no Bridge object
   either. The bridge surface on the live ledger is empty.
3. **The required issuing door does not exist.** For an XRP-XRP
   bridge the pinned preflight requires the issuing door to be the
   root account derived from the seed "masterpassphrase"
   (`r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59`). That account returns
   `actNotFound` on the live ledger. A door account that does not
   exist cannot submit transactions, hold a SignerList, or receive
   funds, so an XRP-XRP bridge with PFTL as the issuing chain
   cannot be operated even if the amendment were enabled. (The
   PFTL genesis account is a different address,
   `r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA`, and would fail the same
   preflight check.)

Against that, the code itself is in good order. The quorum rule is
weight-based (`weight >= quorum`, quorum taken from the door
account's SignerList); attestations are replay-safe by construction
(one entry per signer, re-attestation replaces); claim ids are a
counter that is destroyed after the funds move; bridge creation
rejects equal doors, non-door submitters, mixed XRP/IOU issues, bad
rewards, and self-locking doors. All 24 lab drill cases pass,
including the exact `tem`/`tec` codes the pinned code returns.

## The one structural weakness in the code

The bridge object carries no quorum of its own. The quorum is read
from the door account's SignerList at claim time
(`getSignersListAndQuorum`), and the door owner can change that list
without touching the bridge object. The code itself states the
consequence (XChainBridge.cpp lines 74-77): the witness servers are
trusted "in the sense that if a quorum of them collude, they can
steal the funds put into trust." That is the design — a committee
bridge — not a bug, but it is the whole security assumption, and it
sits in a list the bridge does not control.

## The pfUSDC distinction

The project's own published bridge is not this mechanism. The
pfUSDC page (postfiat.org/pfusdc-trustless-bridge/, fetched by the
probe, HTTP 200, 68,866 bytes) describes a proof-based bridge:
deposits on Arbitrum are proven with an SP1 zkVM proof, verified
on-chain against a pinned checkpoint, with no committee, no
multisig, and no signer fallback. A complete round trip was run on
testnet (Arbitrum Sepolia withdrawal transaction
`0x664b2897…e702c1f9`, exactly 1.000000 USDC released). The XChain
code in postfiatd is upstream XRPL machinery; pfUSDC is a separate
design in the postfiatl1v2 repository. Any assessment that confuses
the two misstates the trust model of both.

## What would change the verdict

- `XChainBridge` enabled on the network (visible in the `feature`
  RPC) plus a created bridge object (visible via `ledger_entry`)
  would move the verdict from "dormant" to "live, assess the
  witness set".
- A door account for an XRP-XRP bridge that exists on the ledger
  would close F-02; as measured, the required root account does not
  exist.
- An independent audit of the pfUSDC contracts and zkVM programs
  (which the pfUSDC page itself lists as remaining work) would be
  needed before any statement about that bridge's safety.
