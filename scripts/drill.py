#!/usr/bin/env python3
"""drill.py — three timed isolated-lab drills for the PFTL XChain bridge.

All three drills run against a LAB-ONLY model (src/xchain_model.py),
a pure-stdlib mirror of the pinned postfiatd XChain rules
(XChainBridge.cpp, XChainAttestations.cpp @ 0085a1ff). No transaction
is submitted, no live bridge interaction happens, no network access
is used. The live inputs used here (validated ledger, amendment
state) come from the read-only probes in outputs/probe-summary.json.

Every case is timed individually with time.monotonic(); the elapsed
time is printed on its PASS/FAIL line and recorded as elapsed_ms in
outputs/derived/drill-results.json, alongside the per-drill and total
wall times.

Drill A — attestation replay: a second attestation from the same
  witness must not double-count toward quorum (onNewAttestations
  replaces; claimHelper sums weights per signer, not per attestation).
Drill B — quorum-threshold failure: below-threshold weight must not
  authorise a claim (tecXCHAIN_CLAIM_NO_QUORUM), and the claim-id
  counter must advance 1, 2, 3 ... with an overflow guard.
Drill C — malformed bridge-account rejection: the bridge-creation
  preflight rules (XChainCreateBridge::preflight) and the attestation
  preflight rules (attestationpreflight) must reject bad inputs with
  the exact tem codes the pinned code returns.

Usage: python3 scripts/drill.py [--outdir outputs]
Exit code 0 only if every case passes.
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from xchain_model import (  # noqa: E402
    MASTERPASSPHRASE_ROOT, TEC_XCHAIN_CLAIM_NO_QUORUM, TEM_MALFORMED,
    TEM_XCHAIN_BAD_PROOF, TEM_XCHAIN_BRIDGE_BAD_ISSUES,
    TEM_XCHAIN_BRIDGE_BAD_MIN_ACCOUNT_CREATE_AMOUNT,
    TEM_XCHAIN_BRIDGE_BAD_REWARD_AMOUNT, TEM_XCHAIN_BRIDGE_NONDOOR_OWNER,
    TEM_XCHAIN_EQUAL_DOOR_ACCOUNTS, TES_SUCCESS, Attestation,
    AttestationSet, check_attestation_public_key, create_claim_id,
    on_claim, on_new_attestations, validate_attestation_preflight,
    validate_create_bridge,
)

# Lab fixtures: a 3-witness bridge, weights 2/2/1, quorum 5.
W1, W2, W3 = "rWitness1", "rWitness2", "rWitness3"
SIGNERS = {W1: 2, W2: 2, W3: 1}
QUORUM = 5
AMOUNT = 1_000_000  # drops
DST = "rDestination"
SENDER = "rSender"


def att(signer, amount=AMOUNT, dst=DST, locking=True, claim_id=1,
        reward=None, **kw):
    return Attestation(
        signer_account=signer, public_key_account=signer,
        sending_account=SENDER, sending_amount_drops=amount,
        was_locking_chain_send=locking, claim_id=claim_id,
        destination=dst, reward_account=reward or ("rReward" + signer[-1]),
        **kw)


def match(amount=AMOUNT, locking=True, dst=DST):
    return {"sending_amount_drops": amount,
            "was_locking_chain_send": locking, "destination": dst}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="outputs")
    args = ap.parse_args()
    outdir = args.outdir
    derived = os.path.join(outdir, "derived")
    os.makedirs(derived, exist_ok=True)

    log_lines = []
    results = {"drills": {}, "total_cases": 0, "total_pass": 0}
    wall_start = time.monotonic()

    def emit(line):
        print(line)
        log_lines.append(line)

    def run_case(drill, case_id, label, fn):
        t0 = time.monotonic()
        try:
            detail = fn()
            ok = True
        except AssertionError as e:
            detail = str(e)
            ok = False
        elapsed_ms = round((time.monotonic() - t0) * 1000, 2)
        status = "PASS" if ok else "FAIL"
        emit(f"{status} {case_id} {label}: {detail} ({elapsed_ms} ms)")
        results["drills"].setdefault(drill, {"cases": []})
        results["drills"][drill]["cases"].append(
            {"id": case_id, "label": label, "status": status,
             "detail": detail, "elapsed_ms": elapsed_ms})
        results["total_cases"] += 1
        if ok:
            results["total_pass"] += 1
        return ok

    def drill_block(drill, label):
        t0 = time.monotonic()
        emit(f"--- Drill {drill}: {label} ---")
        return t0

    def drill_end(drill, t0):
        wall = round((time.monotonic() - t0) * 1000, 2)
        results["drills"][drill]["wall_ms"] = wall
        emit(f"--- Drill {drill} wall: {wall} ms ---")

    # ------------------------------------------------------------------
    # Drill A — attestation replay
    # ------------------------------------------------------------------
    t0 = drill_block("A", "attestation replay must not double-count")

    def a01():
        s = AttestationSet()
        rewards, err = on_claim(s, AMOUNT, True, QUORUM, SIGNERS)
        assert err == TEC_XCHAIN_CLAIM_NO_QUORUM, f"expected no-quorum, got {err}"
        return "weight 0 < quorum 5 -> tecXCHAIN_CLAIM_NO_QUORUM"

    def a02():
        s = AttestationSet()
        rewards, changed = on_new_attestations(
            s, [att(W1), att(W2), att(W3)], match(), QUORUM, SIGNERS)
        assert rewards is not None and len(rewards) == 3, f"rewards={rewards}"
        assert len(s) == 3, f"set size {len(s)}"
        return "3 distinct signers, weight 2+2+1=5 >= quorum 5 -> quorum, 3 reward accounts"

    def a03():
        s = AttestationSet()
        on_new_attestations(s, [att(W1)], match(), QUORUM, SIGNERS)
        on_new_attestations(s, [att(W1)], match(), QUORUM, SIGNERS)
        assert len(s) == 1, f"replay created a second entry: {len(s)}"
        rewards, err = on_claim(s, AMOUNT, True, QUORUM, SIGNERS)
        assert err == TEC_XCHAIN_CLAIM_NO_QUORUM, f"replay reached quorum: {err}"
        return "same signer attests twice -> still 1 entry, weight 2 < 5, no quorum"

    def a04():
        s = AttestationSet()
        on_new_attestations(s, [att(W1, amount=AMOUNT)], match(), QUORUM, SIGNERS)
        on_new_attestations(s, [att(W1, amount=AMOUNT * 2)],
                            match(amount=AMOUNT * 2), QUORUM, SIGNERS)
        assert len(s) == 1, f"set size {len(s)}"
        assert s.attestations[0].sending_amount_drops == AMOUNT * 2
        return "re-attestation with larger amount replaces old one (set stays 1), weight still 2"

    def a05():
        s = AttestationSet()
        outsider = att("rOutsider")
        r = check_attestation_public_key(SIGNERS, "rOutsider", "rOutsider",
                                         False, False, None)
        assert r == "tecNO_PERMISSION", f"expected tecNO_PERMISSION, got {r}"
        rewards, changed = on_new_attestations(
            s, [outsider], match(), QUORUM, SIGNERS)
        assert rewards is None, "outsider attestation counted toward quorum"
        assert len(s) == 0, f"outsider entry not erased by claimHelper: {len(s)}"
        rewards2, err = on_claim(s, AMOUNT, True, QUORUM, SIGNERS)
        assert err == TEC_XCHAIN_CLAIM_NO_QUORUM, "outsider weight counted"
        return "non-signer attestation rejected (tecNO_PERMISSION) and erased before quorum math"

    def a06():
        s = AttestationSet()
        on_new_attestations(s, [att(W1, dst="rOtherDst"), att(W2, dst="rOtherDst"),
                                att(W3, dst="rOtherDst")],
                            match(dst=DST), QUORUM, SIGNERS)
        rewards, err = on_claim(s, AMOUNT, True, QUORUM, SIGNERS)
        assert rewards is not None, "claim path must ignore dst (CheckDst::ignore)"
        s2 = AttestationSet()
        r2, _ = on_new_attestations(
            s2, [att(W1, dst="rOtherDst"), att(W2, dst="rOtherDst"),
                 att(W3, dst="rOtherDst")], match(dst=DST), QUORUM, SIGNERS)
        assert r2 is None, "add-attestation path must check dst (CheckDst::check)"
        return "dst mismatch: excluded on add-attestation path, ignored on claim path"

    def a07():
        s = AttestationSet()
        on_new_attestations(s, [att(W1), att(W2), att(W3)], match(), QUORUM, SIGNERS)
        reduced = {W1: 2, W2: 2}  # W3 removed from the signers list
        rewards, err = on_claim(s, AMOUNT, True, QUORUM, reduced)
        assert err == TEC_XCHAIN_CLAIM_NO_QUORUM, f"stale attestation counted: {err}"
        assert len(s) == 2, f"stale attestation not erased: {len(s)}"
        return "signer removed from list -> its attestation erased, weight 4 < 5, no quorum"

    def a08():
        s = AttestationSet()
        on_new_attestations(s, [att(W1), att(W2)], match(), QUORUM, SIGNERS)
        rewards, err = on_claim(s, AMOUNT, True, QUORUM, SIGNERS)
        assert err == TEC_XCHAIN_CLAIM_NO_QUORUM, "weight 4 reached quorum 5"
        on_new_attestations(s, [att(W3)], match(), QUORUM, SIGNERS)
        rewards, err = on_claim(s, AMOUNT, True, QUORUM, SIGNERS)
        assert rewards is not None and len(rewards) == 3
        return "weighted quorum: 2+2=4 no quorum, +1 = 5 quorum"

    for cid, label, fn in [
            ("A-01", "single attestation, no quorum", a01),
            ("A-02", "three distinct signers reach quorum", a02),
            ("A-03", "replayed attestation does not double-count", a03),
            ("A-04", "re-attestation with larger amount replaces", a04),
            ("A-05", "non-signer attestation rejected and erased", a05),
            ("A-06", "destination checked on add, ignored on claim", a06),
            ("A-07", "removed signer attestation erased", a07),
            ("A-08", "weighted quorum boundary", a08)]:
        run_case("A", cid, label, fn)
    drill_end("A", t0)

    # ------------------------------------------------------------------
    # Drill B — quorum-threshold failure + claim-id counter
    # ------------------------------------------------------------------
    t0 = drill_block("B", "quorum threshold and claim-id counter")

    def b01():
        s = AttestationSet()
        rewards, err = on_claim(s, AMOUNT, True, QUORUM, SIGNERS)
        assert err == TEC_XCHAIN_CLAIM_NO_QUORUM
        return "0 attestations -> tecXCHAIN_CLAIM_NO_QUORUM"

    def b02():
        s = AttestationSet()
        on_new_attestations(s, [att(W1), att(W2)], match(), QUORUM, SIGNERS)
        rewards, err = on_claim(s, AMOUNT, True, QUORUM, SIGNERS)
        assert err == TEC_XCHAIN_CLAIM_NO_QUORUM, f"weight 4 passed quorum 5: {err}"
        return "weight 4 = quorum-1 -> no quorum"

    def b03():
        s = AttestationSet()
        on_new_attestations(s, [att(W1), att(W2), att(W3)], match(), QUORUM, SIGNERS)
        rewards, err = on_claim(s, AMOUNT, True, QUORUM, SIGNERS)
        assert rewards is not None and len(rewards) == 3, f"err={err}"
        return "weight exactly 5 = quorum -> quorum (weight >= quorum)"

    def b04():
        s = AttestationSet()
        big = {W1: 3, W2: 3, W3: 3}
        on_new_attestations(s, [att(W1), att(W2), att(W3)], match(), QUORUM, big)
        rewards, err = on_claim(s, AMOUNT, True, QUORUM, big)
        assert rewards is not None and len(rewards) == 3
        assert rewards == ["rReward1", "rReward2", "rReward3"], f"rewards={rewards}"
        return "weight 9 > quorum 5 -> quorum, reward accounts = the 3 attesters"

    def b05():
        s = AttestationSet()
        on_new_attestations(s, [att(W1), att(W2), att(W3)], match(), QUORUM, SIGNERS)
        rewards, err = on_claim(s, AMOUNT * 2, True, QUORUM, SIGNERS)
        assert err == TEC_XCHAIN_CLAIM_NO_QUORUM, "amount-mismatched attestations matched"
        return "attestations for 1,000,000 do not match a claim for 2,000,000 -> no quorum"

    def b06():
        s = AttestationSet()
        on_new_attestations(s, [att(W1), att(W2), att(W3)], match(), QUORUM, SIGNERS)
        rewards, err = on_claim(s, AMOUNT, False, QUORUM, SIGNERS)
        assert err == TEC_XCHAIN_CLAIM_NO_QUORUM, "wrong-direction attestations matched"
        return "locking-send attestations do not match an issuing-send claim -> no quorum"

    def b07():
        nxt, err = create_claim_id(0)
        assert (nxt, err) == (1, None), f"first claim id {nxt} {err}"
        nxt, err = create_claim_id(1)
        assert nxt == 2
        nxt, err = create_claim_id(2)
        assert nxt == 3
        nxt, err = create_claim_id(0xFFFFFFFF)
        assert nxt is None and err == "tecINTERNAL", f"overflow not guarded: {nxt} {err}"
        return "claim ids advance 1,2,3; counter at 2^32-1 wraps to 0 -> tecINTERNAL"

    for cid, label, fn in [
            ("B-01", "empty attestation set", b01),
            ("B-02", "weight one below quorum", b02),
            ("B-03", "weight exactly quorum", b03),
            ("B-04", "weight above quorum, rewards listed", b04),
            ("B-05", "amount mismatch blocks claim", b05),
            ("B-06", "chain-direction mismatch blocks claim", b06),
            ("B-07", "claim-id counter advances, overflow guarded", b07)]:
        run_case("B", cid, label, fn)
    drill_end("B", t0)

    # ------------------------------------------------------------------
    # Drill C — malformed bridge-account rejection
    # ------------------------------------------------------------------
    t0 = drill_block("C", "malformed bridge-account rejection")

    LOCK = "rLockDoor"
    ISSUE = MASTERPASSPHRASE_ROOT  # XRP issuing door must be the root account
    GENESIS_ISSUER = "rGenesisIssuer"

    def bridge(submitter=LOCK, locking=LOCK, issuing=ISSUE,
               locking_xrp=True, issuing_xrp=True,
               locking_issuer=GENESIS_ISSUER, issuing_issuer=ISSUE,
               reward_xrp=True, reward=1000, min_create=None,
               min_create_xrp=True):
        return validate_create_bridge(
            submitter, locking, issuing, locking_xrp, issuing_xrp,
            locking_issuer, issuing_issuer, reward_xrp, reward,
            min_create, min_create_xrp)

    def c01():
        r = bridge(locking=LOCK, issuing=LOCK)
        assert r == TEM_XCHAIN_EQUAL_DOOR_ACCOUNTS, f"got {r}"
        return "equal door accounts -> temXCHAIN_EQUAL_DOOR_ACCOUNTS"

    def c02():
        r = bridge(submitter="rStranger")
        assert r == TEM_XCHAIN_BRIDGE_NONDOOR_OWNER, f"got {r}"
        return "submitter is neither door -> temXCHAIN_BRIDGE_NONDOOR_OWNER"

    def c03():
        r = bridge(locking_xrp=True, issuing_xrp=False)
        assert r == TEM_XCHAIN_BRIDGE_BAD_ISSUES, f"got {r}"
        return "locking XRP vs issuing IOU -> temXCHAIN_BRIDGE_BAD_ISSUES"

    def c04():
        r1 = bridge(reward=-5)
        r2 = bridge(reward_xrp=False, reward=1000)
        assert r1 == TEM_XCHAIN_BRIDGE_BAD_REWARD_AMOUNT, f"got {r1}"
        assert r2 == TEM_XCHAIN_BRIDGE_BAD_REWARD_AMOUNT, f"got {r2}"
        return "negative reward and non-XRP reward -> temXCHAIN_BRIDGE_BAD_REWARD_AMOUNT"

    def c05():
        r1 = bridge(min_create=1000, min_create_xrp=False)
        r2 = bridge(min_create=0)
        assert r1 == TEM_XCHAIN_BRIDGE_BAD_MIN_ACCOUNT_CREATE_AMOUNT, f"got {r1}"
        assert r2 == TEM_XCHAIN_BRIDGE_BAD_MIN_ACCOUNT_CREATE_AMOUNT, f"got {r2}"
        return "non-XRP and zero min-account-create amount -> temXCHAIN_BRIDGE_BAD_MIN_ACCOUNT_CREATE_AMOUNT"

    def c06():
        r = bridge(issuing="rNotRoot")
        assert r == TEM_XCHAIN_BRIDGE_BAD_ISSUES, f"got {r}"
        return "XRP issuing door that is not the root account -> temXCHAIN_BRIDGE_BAD_ISSUES"

    def c07():
        # The self-lock check is last in preflight: the submitter must
        # first pass the door-owner check, so submit as the locking door.
        r = bridge(submitter="rIssuerSelf", locking="rIssuerSelf",
                   locking_issuer="rIssuerSelf")
        assert r == TEM_XCHAIN_BRIDGE_BAD_ISSUES, f"got {r}"
        return "locking door locking its own asset -> temXCHAIN_BRIDGE_BAD_ISSUES"

    def c08():
        a = att(W1, public_key_type="unknown-key-type")
        r = validate_attestation_preflight(a, "XRP")
        assert r == TEM_MALFORMED, f"got {r}"
        return "attestation with unknown public-key type -> temMALFORMED"

    def c09():
        a1 = att(W1, amount=0)
        a2 = att(W1, amount=AMOUNT, issue="USD/rIssuer")
        a3 = att(W1, signature_valid=False)
        assert validate_attestation_preflight(a1, "XRP") == TEM_XCHAIN_BAD_PROOF
        assert validate_attestation_preflight(a2, "XRP") == TEM_XCHAIN_BAD_PROOF
        assert validate_attestation_preflight(a3, "XRP") == TEM_XCHAIN_BAD_PROOF
        return "zero amount, wrong issue, bad signature -> temXCHAIN_BAD_PROOF"

    for cid, label, fn in [
            ("C-01", "equal door accounts rejected", c01),
            ("C-02", "non-door submitter rejected", c02),
            ("C-03", "mixed XRP/IOU issues rejected", c03),
            ("C-04", "bad signature reward rejected", c04),
            ("C-05", "bad min-account-create amount rejected", c05),
            ("C-06", "non-root XRP issuing door rejected", c06),
            ("C-07", "self-locking door rejected", c07),
            ("C-08", "bad public-key type rejected", c08),
            ("C-09", "bad attestation proof rejected", c09)]:
        run_case("C", cid, label, fn)
    drill_end("C", t0)

    total_wall = round((time.monotonic() - wall_start) * 1000, 2)
    results["total_wall_ms"] = total_wall
    emit(f"TOTAL: {results['total_pass']}/{results['total_cases']} PASS "
         f"(wall {total_wall} ms)")

    with open(os.path.join(derived, "drill-results.json"), "w") as f:
        json.dump(results, f, indent=1, sort_keys=True)
    with open(os.path.join(outdir, "drill-run.log"), "w") as f:
        f.write("\n".join(log_lines) + "\n")

    if results["total_pass"] != results["total_cases"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
