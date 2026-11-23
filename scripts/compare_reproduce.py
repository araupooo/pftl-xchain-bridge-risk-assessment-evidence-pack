#!/usr/bin/env python3
"""compare_reproduce.py — compare the fresh-clone reproduction against the
shipped results. Prints one PASS/FAIL line per check and exits 0 only if
every check passes. Ledger numbers are expected to ADVANCE between the
shipped probe and the fresh probe; the checks assert the direction and
the invariants, not exact equality of live values.

Reads outputs/derived/* (shipped) and outputs/fresh-clone/derived/*.
"""

import json
import os
import sys

SHIPPED = "outputs/derived"
FRESH = "outputs/fresh-clone/derived"


def load(d, name):
    with open(os.path.join(d, name)) as f:
        return json.load(f)


def main():
    shipped_probe = load(SHIPPED, "probe-summary.json")
    fresh_probe = load(FRESH, "probe-summary.json")
    shipped_drill = load(SHIPPED, "drill-results.json")
    fresh_drill = load(FRESH, "drill-results.json")

    checks = []

    def check(name, ok, detail):
        checks.append(ok)
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")

    check("build version unchanged",
          fresh_probe.get("build_version") == shipped_probe.get("build_version") == "1.0.9",
          f"shipped={shipped_probe.get('build_version')} fresh={fresh_probe.get('build_version')}")
    check("network id unchanged",
          fresh_probe.get("network_id") == shipped_probe.get("network_id") == 2025,
          f"network_id={fresh_probe.get('network_id')}")
    check("validated ledger advanced",
          (fresh_probe.get("validated_ledger_seq") or 0) > (shipped_probe.get("validated_ledger_seq") or 0),
          f"shipped {shipped_probe.get('validated_ledger_seq')} -> fresh {fresh_probe.get('validated_ledger_seq')}")
    check("complete-ledgers floor unchanged",
          (fresh_probe.get("complete_ledgers") or "").split("-")[0] ==
          (shipped_probe.get("complete_ledgers") or "").split("-")[0] == "8200054",
          f"floor={(fresh_probe.get('complete_ledgers') or '').split('-')[0]}")
    check("quorum unchanged",
          fresh_probe.get("validation_quorum") == shipped_probe.get("validation_quorum") == 17,
          f"quorum={fresh_probe.get('validation_quorum')}")
    check("validator-list sequence unchanged",
          (fresh_probe.get("validator_list") or {}).get("blob_sequence") ==
          (shipped_probe.get("validator_list") or {}).get("blob_sequence") == 30,
          f"VL sequence={(fresh_probe.get('validator_list') or {}).get('blob_sequence')}")
    check("validator-list validators unchanged",
          (fresh_probe.get("validator_list") or {}).get("validators_in_blob") ==
          (shipped_probe.get("validator_list") or {}).get("validators_in_blob") == 25,
          f"validators={(fresh_probe.get('validator_list') or {}).get('validators_in_blob')}")
    check("XChainBridge still disabled",
          (fresh_probe.get("xchain_amendments") or {}).get("XChainBridge", {}).get("enabled") is False
          and (shipped_probe.get("xchain_amendments") or {}).get("XChainBridge", {}).get("enabled") is False,
          f"fresh={fresh_probe.get('xchain_amendments')} shipped={shipped_probe.get('xchain_amendments')}")
    check("fixXChainRewardRounding still disabled",
          (fresh_probe.get("xchain_amendments") or {}).get("fixXChainRewardRounding", {}).get("enabled") is False
          and (shipped_probe.get("xchain_amendments") or {}).get("fixXChainRewardRounding", {}).get("enabled") is False,
          "both runs report fixXChainRewardRounding disabled")
    check("genesis account still exists with same balance",
          (fresh_probe.get("genesis_account") or {}).get("balance_drops") ==
          (shipped_probe.get("genesis_account") or {}).get("balance_drops") == "96999999999999880",
          f"balance={fresh_probe.get('genesis_account', {}).get('balance_drops')}")
    check("masterpassphrase root still absent",
          (fresh_probe.get("xrpl_root_account") or {}).get("error") ==
          (shipped_probe.get("xrpl_root_account") or {}).get("error") == "actNotFound",
          f"error={fresh_probe.get('xrpl_root_account', {}).get('error')}")
    check("fabricated bridge still entryNotFound",
          (fresh_probe.get("fabricated_bridge_ledger_entry") or {}).get("error") ==
          (shipped_probe.get("fabricated_bridge_ledger_entry") or {}).get("error") == "entryNotFound",
          f"error={fresh_probe.get('fabricated_bridge_ledger_entry', {}).get('error')}")
    check("drill pass counts equal",
          (fresh_drill.get("total_pass"), fresh_drill.get("total_cases")) ==
          (shipped_drill.get("total_pass"), shipped_drill.get("total_cases")) == (24, 24),
          f"fresh {fresh_drill.get('total_pass')}/{fresh_drill.get('total_cases')}, "
          f"shipped {shipped_drill.get('total_pass')}/{shipped_drill.get('total_cases')}")
    check("drill case ids identical",
          [c["id"] for d in fresh_drill["drills"].values() for c in d["cases"]] ==
          [c["id"] for d in shipped_drill["drills"].values() for c in d["cases"]],
          "24 case ids match in order")
    check("fresh-clone cadence sane",
          (fresh_probe.get("cadence") or {}).get("seconds_per_ledger") is not None
          and 2.0 < (fresh_probe.get("cadence") or {}).get("seconds_per_ledger", 0) < 4.0,
          f"{(fresh_probe.get('cadence') or {}).get('seconds_per_ledger')} s/ledger")

    n_pass = sum(checks)
    print(f"{n_pass}/{len(checks)} compare checks PASS")
    return 0 if n_pass == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
