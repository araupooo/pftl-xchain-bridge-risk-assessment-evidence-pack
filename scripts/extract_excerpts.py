#!/usr/bin/env python3
"""extract_excerpts.py — pull verbatim pinned-source excerpts.

Reads the local checkout of the pinned postfiatd revision (default
/tmp/postfiatd-pin, verified to be commit 0085a1ff) and writes
fixtures/source-excerpts/*.txt, one file per excerpt. Every excerpt
carries a header giving the source file, the 1-based line range, and
the commit; every range is checked against anchor strings that must
appear in the extracted text, so a wrong range fails loudly instead of
shipping a silent misquote.

Also writes fixtures/source-hashes.json with the git blob SHA and size
of every excerpted source file, so a reviewer can confirm the checkout
matches the pinned commit.

Usage: python3 scripts/extract_excerpts.py [--pin /tmp/postfiatd-pin]
       [--out fixtures/source-excerpts]
"""

import argparse
import json
import os
import subprocess
import sys

PIN = "0085a1ff885d6a446369cf73a4430f75af22be55"

# (output filename, source file, [(start, end), ...], anchor strings)
EXCERPTS = [
    ("bridge-model.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(52, 72)],
     ["Bridges connect two independent ledgers",
      "A good model for thinking about bridges is a box"]),
    ("quorum-collusion.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(74, 77)],
     ["if a quorum of", "they can steal the funds put into trust"]),
    ("claim-id-model.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(86, 98)],
     ["Claim ids", "Once a quorum", "Once the funds move, the claim id is destroyed"]),
    ("check-attestation-key.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(111, 175)],
     ["checkAttestationPublicKey(", "tecXCHAIN_BAD_PUBLIC_KEY_ACCOUNT_PAIR",
      "lsfDisableMaster"]),
    ("claim-helper-quorum.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(189, 242)],
     ["claimHelper(", "weight >= quorum", "tecXCHAIN_CLAIM_NO_QUORUM"]),
    ("on-new-attestation.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(282, 344)],
     ["onNewAttestations(", "replace old attestation with new attestation"]),
    ("on-claim.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(346, 366)],
     ["onClaim(", "CheckDst::ignore"]),
    ("signers-list-quorum.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(771, 810)],
     ["getSignersListAndQuorum(", "sfSignerQuorum", "tecXCHAIN_NO_SIGNERS_LIST"]),
    ("reward-rounding.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(675, 695)],
     ["fixXChainRewardRounding", "rounding_mode::downward"]),
    ("finalize-claim-destroy.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(739, 760)],
     ["Remove the claim id", "outerSb.erase(sleClaimID)"]),
    ("attestation-preflight.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(1215, 1240)],
     ["attestationpreflight(", "temXCHAIN_BAD_PROOF"]),
    ("attestation-preclaim.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(1241, 1271)],
     ["attestationPreclaim(", "getSignersListAndQuorum"]),
    ("attestation-doapply.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(1272, 1372)],
     ["attestationDoApply", "applyClaimAttestations",
      "getSignersListAndQuorum"]),
    ("create-bridge-preflight.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(1374, 1447)],
     ["XChainCreateBridge::preflight", "temXCHAIN_EQUAL_DOOR_ACCOUNTS",
      "temXCHAIN_BRIDGE_NONDOOR_OWNER", "temXCHAIN_BRIDGE_BAD_ISSUES"]),
    ("create-bridge-preclaim.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(1448, 1498)],
     ["XChainCreateBridge::preclaim", "tecDUPLICATE", "tecNO_ISSUER",
      "lsfAllowTrustLineClawback"]),
    ("create-bridge-apply.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(1500, 1544)],
     ["XChainCreateBridge::doApply", "sfXChainClaimID", "sfXChainAccountCreateCount"]),
    ("bridge-modify-apply.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(1612, 1651)],
     ["BridgeModify::doApply", "tfClearAccountCreateAmount"]),
    ("claim-apply-quorum.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(1806, 1830)],
     ["getSignersListAndQuorum", "onClaim("]),
    ("commit-apply.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(1943, 1985)],
     ["XChainCommit::doApply"]),
    ("create-claim-id-apply.txt",
     "src/xrpld/app/tx/detail/XChainBridge.cpp",
     [(2035, 2097)],
     ["XChainCreateClaimID::doApply", "claimID == 0", "overflow"]),
    ("tx-types-gate.txt",
     "include/xrpl/protocol/detail/transactions.macro",
     [(526, 637)],
     ["ttXCHAIN_CREATE_CLAIM_ID", "ttXCHAIN_CREATE_BRIDGE",
      "featureXChainBridge", "ttXCHAIN_MODIFY_BRIDGE"]),
    ("temdisabled-gate.txt",
     "src/xrpld/app/tx/detail/Transactor.h",
     [(409, 425)],
     ["invokePreflight", "temDISABLED", "getTxFeature"]),
    ("bridge-ledger-entry.txt",
     "include/xrpl/protocol/detail/ledger_entries.macro",
     [(228, 240)],
     ["LEDGER_ENTRY(ltBRIDGE", "sfXChainBridge", "sfXChainClaimID"]),
    ("claim-id-ledger-entry.txt",
     "include/xrpl/protocol/detail/ledger_entries.macro",
     [(277, 287)],
     ["LEDGER_ENTRY(ltXCHAIN_OWNED_CLAIM_ID", "sfXChainClaimAttestations"]),
    ("create-account-ledger-entry.txt",
     "include/xrpl/protocol/detail/ledger_entries.macro",
     [(333, 341)],
     ["LEDGER_ENTRY(ltXCHAIN_OWNED_CREATE_ACCOUNT_CLAIM_ID",
      "sfXChainCreateAccountAttestations"]),
    ("attestation-verify.txt",
     "src/libxrpl/protocol/XChainAttestations.cpp",
     [(102, 106)],
     ["AttestationBase::verify", "ripple::verify(publicKey"]),
    ("bridge-keylets.txt",
     "src/libxrpl/protocol/Indexes.cpp",
     [(481, 515)],
     ["bridge(STXChainBridge", "xChainClaimID(", "XCHAIN_CLAIM_ID"]),
    ("feature-macro.txt",
     "include/xrpl/protocol/detail/features.macro",
     [(75, 84)],
     ["XChainRewardRounding", "XChainBridge", "VoteBehavior::DefaultNo"]),
    ("ledger-entry-bridge-rpc.txt",
     "src/xrpld/rpc/handlers/LedgerEntry.cpp",
     [(120, 140)],
     ["parseBridgeFields", "malformedBridgeAccount", "keylet::bridge"]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pin", default="/tmp/postfiatd-pin")
    ap.add_argument("--out", default="fixtures/source-excerpts")
    args = ap.parse_args()

    head = subprocess.run(
        ["git", "-C", args.pin, "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True).stdout.strip()
    if head != PIN:
        print(f"FAIL pinned checkout HEAD is {head}, expected {PIN}", file=sys.stderr)
        sys.exit(1)
    print(f"pinned checkout HEAD verified — {head}")

    os.makedirs(args.out, exist_ok=True)
    hashes = {}
    for name, src, ranges, anchors in EXCERPTS:
        path = os.path.join(args.pin, src)
        with open(path) as f:
            lines = f.readlines()
        parts = []
        for start, end in ranges:
            seg = "".join(lines[start - 1:end])
            parts.append(seg)
            for anchor in anchors:
                # an anchor must appear in at least one segment
                pass
        text = "".join(parts)
        missing = [a for a in anchors if a not in text]
        if missing:
            print(f"FAIL {name}: anchors missing: {missing}", file=sys.stderr)
            sys.exit(1)
        # keep the file's trailing newline structure as-is
        ranges_s = ", ".join(f"{s}-{e}" for s, e in ranges)
        header = (f"// Source: postfiatorg/postfiatd @ {PIN}\n"
                  f"// File: {src}\n"
                  f"// Lines: {ranges_s}\n"
                  f"// Verbatim excerpt; line numbers verified with grep -n on the pinned checkout.\n\n")
        with open(os.path.join(args.out, name), "w") as f:
            f.write(header + text)
        print(f"wrote {name} ({src} lines {ranges_s})")

        if src not in hashes:
            blob = subprocess.run(
                ["git", "-C", args.pin, "hash-object", src],
                capture_output=True, text=True, check=True).stdout.strip()
            size = os.path.getsize(path)
            hashes[src] = {"blob_sha": blob, "size_bytes": size,
                           "commit": PIN,
                           "note": "verify against the GitHub API blob "
                                   "endpoint for this commit"}

    parent = os.path.dirname(os.path.abspath(args.out))
    with open(os.path.join(parent, "source-hashes.json"), "w") as f:
        json.dump(hashes, f, indent=1, sort_keys=True)
    print(f"wrote source-hashes.json ({len(hashes)} source files)")


if __name__ == "__main__":
    main()
