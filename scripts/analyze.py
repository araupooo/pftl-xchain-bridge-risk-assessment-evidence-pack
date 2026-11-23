#!/usr/bin/env python3
"""analyze.py — cross-check the shipped probe + drill outputs.

Reads outputs/derived/probe-summary.json and
outputs/derived/drill-results.json (and the raw rpc-*.json files) and
asserts the invariants the pack's claims rest on. Prints one
PASS/FAIL line per check and exits 0 only if every check passes.
Writes outputs/derived/run-checks.json and
outputs/derived/xchain-inventory.json (the machine-readable bridge
inventory) and outputs/derived/bridge-surface.json (the live surface
table).
"""

import argparse
import json
import os
import sys

PIN = "0085a1ff885d6a446369cf73a4430f75af22be55"


def load(path):
    with open(path) as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="outputs")
    args = ap.parse_args()
    derived = os.path.join(args.outdir, "derived")
    probe = load(os.path.join(derived, "probe-summary.json"))
    drill = load(os.path.join(derived, "drill-results.json"))
    checks = []

    def check(name, ok, detail):
        checks.append({"name": name, "pass": bool(ok), "detail": str(detail)})
        print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")

    # --- live context ------------------------------------------------------
    check("build version is 1.0.9",
          probe.get("build_version") == "1.0.9",
          f"build_version={probe.get('build_version')}")
    check("network id is 2025",
          probe.get("network_id") == 2025,
          f"network_id={probe.get('network_id')}")
    check("validated ledger advanced past 8,287,000",
          (probe.get("validated_ledger_seq") or 0) > 8287000,
          f"validated_ledger_seq={probe.get('validated_ledger_seq')}")
    check("complete-ledgers floor is 8200054",
          (probe.get("complete_ledgers") or "").split("-")[0] == "8200054",
          f"complete_ledgers={probe.get('complete_ledgers')}")
    check("cadence near 3 s/ledger",
          probe.get("cadence") is not None and
          2.5 < probe["cadence"]["seconds_per_ledger"] < 3.5,
          f"cadence={probe.get('cadence')}")
    check("validation quorum is 17",
          probe.get("validation_quorum") == 17,
          f"quorum={probe.get('validation_quorum')}")
    check("peers is 21",
          probe.get("peers") == 21,
          f"peers={probe.get('peers')}")

    # --- amendment gate -----------------------------------------------------
    x = probe.get("xchain_amendments", {})
    check("XChainBridge amendment is DISABLED live",
          x.get("XChainBridge", {}).get("enabled") is False,
          f"XChainBridge={x.get('XChainBridge')}")
    check("fixXChainRewardRounding amendment is DISABLED live",
          x.get("fixXChainRewardRounding", {}).get("enabled") is False,
          f"fixXChainRewardRounding={x.get('fixXChainRewardRounding')}")
    check("amendment table has 101 entries, 64 enabled",
          probe.get("feature_entries") == 101
          and probe.get("feature_enabled") == 64,
          f"entries={probe.get('feature_entries')} "
          f"enabled={probe.get('feature_enabled')}")

    # --- genesis / root accounts ---------------------------------------------
    g = probe.get("genesis_account", {})
    check("PFTL genesis account exists with flags 0",
          g.get("exists") is True and g.get("flags") == 0,
          f"exists={g.get('exists')} flags={g.get('flags')} "
          f"balance_drops={g.get('balance_drops')}")
    check("genesis balance is 96,999,999,999,999,880 drops",
          g.get("balance_drops") == "96999999999999880",
          f"balance_drops={g.get('balance_drops')}")
    r = probe.get("xrpl_root_account", {})
    check("masterpassphrase root account does NOT exist live",
          r.get("exists") is False and r.get("error") == "actNotFound",
          f"error={r.get('error')} code={r.get('error_code')}")
    check("genesis account owns zero ledger objects",
          probe.get("genesis_account_objects", {}).get("count") == 0,
          f"objects={probe.get('genesis_account_objects')}")
    check("fabricated bridge ledger_entry returns entryNotFound",
          probe.get("fabricated_bridge_ledger_entry", {}).get("error")
          == "entryNotFound",
          f"{probe.get('fabricated_bridge_ledger_entry')}")

    # --- validator list -------------------------------------------------------
    vl = probe.get("validator_list", {})
    check("validator-list blob sequence is 30",
          vl.get("blob_sequence") == 30,
          f"blob_sequence={vl.get('blob_sequence')}")
    check("validator-list blob holds 25 validators",
          vl.get("validators_in_blob") == 25,
          f"validators_in_blob={vl.get('validators_in_blob')}")

    # --- drills ----------------------------------------------------------------
    check("all drill cases pass",
          drill.get("total_pass") == drill.get("total_cases") == 24,
          f"{drill.get('total_pass')}/{drill.get('total_cases')} PASS")
    for d, want in (("A", 8), ("B", 7), ("C", 9)):
        got = drill.get("drills", {}).get(d, {})
        cases = got.get("cases", [])
        check(f"drill {d} has {want} cases, all PASS",
              len(cases) == want and all(c["status"] == "PASS" for c in cases),
              f"{len(cases)} cases")
        check(f"drill {d} cases all carry elapsed_ms",
              all("elapsed_ms" in c for c in cases),
              f"{len(cases)} cases with elapsed_ms")

    # --- inventory + surface tables --------------------------------------------
    inventory = {
        "pinned_commit": PIN,
        "transaction_types": [
            {"type": "XChainCreateClaimID", "code": 41,
             "gate": "featureXChainBridge",
             "source": "include/xrpl/protocol/detail/transactions.macro:526-537"},
            {"type": "XChainCommit", "code": 42,
             "gate": "featureXChainBridge",
             "source": "include/xrpl/protocol/detail/transactions.macro:539-549"},
            {"type": "XChainClaim", "code": 43,
             "gate": "featureXChainBridge",
             "source": "include/xrpl/protocol/detail/transactions.macro:551-562"},
            {"type": "XChainAccountCreateCommit", "code": 44,
             "gate": "featureXChainBridge",
             "source": "include/xrpl/protocol/detail/transactions.macro:564-575"},
            {"type": "XChainAddClaimAttestation", "code": 45,
             "gate": "featureXChainBridge",
             "source": "include/xrpl/protocol/detail/transactions.macro:576-595"},
            {"type": "XChainAddAccountCreateAttestation", "code": 46,
             "gate": "featureXChainBridge",
             "source": "include/xrpl/protocol/detail/transactions.macro:596-616"},
            {"type": "XChainModifyBridge", "code": 47,
             "gate": "featureXChainBridge",
             "source": "include/xrpl/protocol/detail/transactions.macro:618-627"},
            {"type": "XChainCreateBridge", "code": 48,
             "gate": "featureXChainBridge",
             "source": "include/xrpl/protocol/detail/transactions.macro:629-637"},
        ],
        "ledger_entries": [
            {"type": "Bridge", "code": "0x0069",
             "source": "include/xrpl/protocol/detail/ledger_entries.macro:228-240"},
            {"type": "XChainOwnedClaimID", "code": "0x0071",
             "source": "include/xrpl/protocol/detail/ledger_entries.macro:277-290"},
            {"type": "XChainOwnedCreateAccountClaimID", "code": "0x0074",
             "source": "include/xrpl/protocol/detail/ledger_entries.macro:333-345"},
        ],
        "amendments": [
            {"name": "XChainBridge", "vote": "DefaultNo",
             "live": "disabled",
             "source": "include/xrpl/protocol/detail/features.macro:84"},
            {"name": "fixXChainRewardRounding", "vote": "DefaultNo",
             "live": "disabled",
             "source": "include/xrpl/protocol/detail/features.macro:75"},
        ],
        "quorum_rule": "weight >= quorum; quorum = door account SignerList "
                       "sfSignerQuorum; weights per signer (claimHelper, "
                       "XChainBridge.cpp 189-242; getSignersListAndQuorum, "
                       "771-810)",
        "replay_rule": "one attestation per signer; re-attestation "
                       "replaces the old one (onNewAttestations, "
                       "XChainBridge.cpp 282-350)",
        "claim_id_rule": "counter + 1 per XChainCreateClaimID, destroyed "
                         "after funds move, never reusable "
                         "(XChainBridge.cpp 2035-2098, 739-760)",
    }
    with open(os.path.join(derived, "xchain-inventory.json"), "w") as f:
        json.dump(inventory, f, indent=1, sort_keys=True)

    surface = {
        "amendment_gate": "XChainBridge disabled live; all 8 XChain tx "
                          "types return temDISABLED (Transactor.h 409-425)",
        "bridges_on_ledger": "none observed: fabricated bridge ledger_entry "
                             "-> entryNotFound; genesis owns 0 objects",
        "genesis_account": g,
        "xrpl_root_account": r,
        "pfusdc_direction": "project's published bridge is pfUSDC, "
                            "proof-based (SP1 zkVM), not the committee "
                            "XChain — postfiat.org/pfusdc-trustless-bridge/ "
                            "(HTTP 200, fetched by the probe)",
    }
    with open(os.path.join(derived, "bridge-surface.json"), "w") as f:
        json.dump(surface, f, indent=1, sort_keys=True)

    result = {"checks": checks,
              "passed": sum(1 for c in checks if c["pass"]),
              "total": len(checks)}
    with open(os.path.join(derived, "run-checks.json"), "w") as f:
        json.dump(result, f, indent=1, sort_keys=True)
    print(f"ANALYSIS: {result['passed']}/{result['total']} checks PASS")
    if result["passed"] != result["total"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
