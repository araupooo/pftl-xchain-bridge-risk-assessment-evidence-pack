#!/usr/bin/env python3
"""probe_all.py — read-only live probes of the PFTL testnet XChain surface.

Writes UNEDITED probe outputs under outputs/ (or --outdir) and a
human-readable probe-run.log. No transaction is submitted, no vote is
cast, no bridge interaction happens, and NO peer connection is opened
to the live network: every probe is an HTTP POST to the public
JSON-RPC endpoint or an HTTP GET of a public document.

What is probed, and why:
- server_info / ledger_current / ledger_closed / fee: live context
  (build, network id, validated ledger, cadence).
- feature: the live amendment table — XChainBridge and
  fixXChainRewardRounding enabled or not (the gate for every XChain
  transaction type, transactions.macro lines 526-637).
- account_info on the PFTL genesis account
  r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA and on the masterpassphrase-derived
  root account r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59 (the address the
  pinned XChainCreateBridge preflight requires as the XRP issuing
  door): does either exist, and with what flags/balance?
- account_objects on the genesis account: does it own any Bridge,
  XChainOwnedClaimID or XChainOwnedCreateAccountClaimID object?
- ledger_entry for a fabricated bridge (genesis locking door, XRP
  issues, masterpassphrase root as issuing door): entryNotFound is
  the expected answer when no such bridge object exists.
- VHS amendments info (public validator-history service): the
  XChainBridge / fixXChainRewardRounding registry entries.
- postfiat.org pfusdc-trustless-bridge page: the project's published
  bridge direction (proof-based pfUSDC, not the committee XChain).
- Explorer homepage + /health, and the validator list document.

Usage: python3 scripts/probe_all.py [--outdir outputs] [--skip-cadence]
The cadence measurement takes ~60 s (two ledger_current reads).
"""

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

RPC = "https://rpc.testnet.postfiat.org/"
VL_URL = "https://postfiat.org/testnet_vl.json"
VHS_AMENDMENTS_INFO = "https://vhs.testnet.postfiat.org/v1/network/amendments/info"
PFUSDC_PAGE = "https://postfiat.org/pfusdc-trustless-bridge/"
EXPLORER_URLS = [
    "https://explorer.testnet.postfiat.org/",
    "https://explorer.testnet.postfiat.org/health",
    "https://explorer.postfiat.org/",
]

GENESIS = "r4vhrMChCsaoFsBoCkRTRGUuc1njfr7bmA"
XRPL_ROOT = "r9cZA1mLK5R5Am25ArfXFmqgNwjZgnfk59"


def utcnow():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rpc(method, params=None, fname=None):
    body = {"method": method, "params": [params] if params is not None else [{}]}
    req = urllib.request.Request(
        RPC, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, {"http_error": e.code,
                        "body": e.read().decode(errors="replace")[:500]}
    except Exception as e:
        return None, {"error": str(e)}


def http_get(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:500]
    except Exception as e:
        return None, str(e).encode()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--skip-cadence", action="store_true")
    args = ap.parse_args()
    import os
    outdir = args.outdir
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(os.path.join(outdir, "derived"), exist_ok=True)
    log_lines = []

    def log(msg):
        line = f"[{utcnow()}] {msg}"
        print(line)
        log_lines.append(line)

    def save_rpc(name, method, params, status, data):
        fname = os.path.join(outdir, f"rpc-{name}.json")
        with open(fname, "w") as f:
            json.dump({"http_status": status, "method": method,
                       "params": params, "probed_at_utc": utcnow(),
                       "response": data}, f, indent=1, sort_keys=True)
        log(f"rpc {method} [{name}] -> HTTP {status} (saved {fname})")
        return fname

    log("probe start — read-only RPC + public GETs only; no transactions, "
        "no bridge interaction, no peer connections")
    calls = 0
    results = {}

    # --- JSON-RPC probes, no params --------------------------------------
    for method in ["server_info", "ledger_current", "ledger_closed",
                   "fee", "feature"]:
        status, data = rpc(method)
        calls += 1
        results[method] = data
        save_rpc(method, method, {}, status, data)
        time.sleep(0.5)

    # --- account_info: PFTL genesis + masterpassphrase root --------------
    for name, account in [("account_info-genesis", GENESIS),
                          ("account_info-xrpl-root", XRPL_ROOT)]:
        params = {"account": account, "ledger_index": "validated"}
        status, data = rpc("account_info", params)
        calls += 1
        results[name] = data
        save_rpc(name, "account_info", params, status, data)
        time.sleep(0.5)

    # --- account_objects: what the genesis account owns ------------------
    params = {"account": GENESIS, "ledger_index": "validated"}
    status, data = rpc("account_objects", params)
    calls += 1
    results["account_objects-genesis"] = data
    save_rpc("account_objects-genesis", "account_objects", params,
             status, data)
    time.sleep(0.5)

    # --- ledger_entry: fabricated bridge (genesis door, XRP issues) ------
    bridge = {"LockingChainDoor": GENESIS,
              "LockingChainIssue": {"currency": "XRP"},
              "IssuingChainDoor": XRPL_ROOT,
              "IssuingChainIssue": {"currency": "XRP"}}
    params = {"bridge": bridge, "bridge_account": GENESIS,
              "ledger_index": "validated"}
    status, data = rpc("ledger_entry", params)
    calls += 1
    results["ledger_entry-bridge-genesis"] = data
    save_rpc("ledger_entry-bridge-genesis", "ledger_entry", params,
             status, data)
    time.sleep(0.5)

    # --- Validator list document ------------------------------------------
    status, body = http_get(VL_URL)
    calls += 1
    vl_path = os.path.join(outdir, "testnet_vl.json")
    with open(vl_path, "wb") as f:
        f.write(body if isinstance(body, bytes) else body.encode())
    log(f"GET {VL_URL} -> HTTP {status}, {len(body)} bytes (saved {vl_path})")
    vl_info = {"http_status": status, "bytes": len(body)}
    if status == 200:
        try:
            vl = json.loads(body)
            blobs = vl.get("blobs_v2", [])
            vl_info["format"] = "v2 (blobs_v2)"
            vl_info["publisher_key"] = vl.get("public_key")
            vl_info["manifest_chars"] = len(vl.get("manifest", ""))
            if blobs:
                # The blob is base64 of a JSON document (same shape the
                # overlay pack decoded): sequence / effective /
                # expiration / validators.
                raw = __import__("base64").b64decode(blobs[0].get("blob", ""))
                b = json.loads(raw)
                vl_info["blob_sequence"] = b.get("sequence")
                vl_info["blob_effective"] = b.get("effective")
                vl_info["blob_expiration"] = b.get("expiration")
                vl_info["validators_in_blob"] = len(b.get("validators", []))
                vl_info["blob_bytes_decoded"] = len(raw)
                vl_info["signature_chars"] = len(blobs[0].get("signature", ""))
        except Exception as e:
            vl_info["parse_error"] = str(e)

    # --- VHS amendments info ----------------------------------------------
    status, body = http_get(VHS_AMENDMENTS_INFO)
    calls += 1
    vhs_path = os.path.join(outdir, "vhs-amendments-info.json")
    with open(vhs_path, "wb") as f:
        f.write(body if isinstance(body, bytes) else body.encode())
    log(f"GET {VHS_AMENDMENTS_INFO} -> HTTP {status}, {len(body)} bytes "
        f"(saved {vhs_path})")
    vhs_info = {"http_status": status, "bytes": len(body)}
    if status == 200:
        try:
            vhs = json.loads(body)
            vhs_info["count"] = vhs.get("count")
            for a in vhs.get("amendments", []):
                if a.get("name") in ("XChainBridge", "fixXChainRewardRounding"):
                    vhs_info[a["name"]] = {"id": a.get("id"),
                                           "deprecated": a.get("deprecated")}
        except Exception as e:
            vhs_info["parse_error"] = str(e)

    # --- PostFiat pfUSDC bridge page ---------------------------------------
    status, body = http_get(PFUSDC_PAGE)
    calls += 1
    pf_path = os.path.join(outdir, "postfiat-pfusdc-bridge.html")
    with open(pf_path, "wb") as f:
        f.write(body if isinstance(body, bytes) else body.encode())
    log(f"GET {PFUSDC_PAGE} -> HTTP {status}, {len(body)} bytes (saved {pf_path})")
    pfusdc_info = {"http_status": status, "bytes": len(body),
                   "sha256": sha256_file(pf_path)}

    # --- Explorer GETs ------------------------------------------------------
    explorer = {}
    for url in EXPLORER_URLS:
        status, body = http_get(url)
        calls += 1
        explorer[url] = {"http_status": status,
                         "body_head": body[:200].decode(errors="replace")}
        log(f"GET {url} -> HTTP {status}")

    # --- Cadence: two ledger_current reads ~60 s apart ----------------------
    cadence = None
    if not args.skip_cadence:
        s1, d1 = rpc("ledger_current")
        seq1 = d1.get("result", {}).get("ledger_current_index")
        t1 = time.time()
        log(f"cadence start: ledger_current_index={seq1}")
        time.sleep(60)
        s2, d2 = rpc("ledger_current")
        seq2 = d2.get("result", {}).get("ledger_current_index")
        elapsed = time.time() - t1
        calls += 2
        if seq1 and seq2:
            cadence = {"start_seq": seq1, "end_seq": seq2,
                       "ledgers": seq2 - seq1,
                       "elapsed_seconds": round(elapsed, 1),
                       "seconds_per_ledger": round(
                           elapsed / max(seq2 - seq1, 1), 3)}
            log(f"cadence: {seq1} -> {seq2} in {elapsed:.1f} s "
                f"({cadence['seconds_per_ledger']} s/ledger)")

    # --- Summary ------------------------------------------------------------
    info = results.get("server_info", {}).get("result", {}).get("info", {})
    vl_seq = results.get("ledger_current", {}).get("result", {}).get(
        "ledger_current_index")
    feat = results.get("feature", {}).get("result", {}).get("features", {})
    xchain = {}
    for v in feat.values():
        if v.get("name") in ("XChainBridge", "fixXChainRewardRounding"):
            xchain[v["name"]] = {"enabled": v.get("enabled"),
                                 "supported": v.get("supported")}
    genesis = results.get("account_info-genesis", {}).get("result", {})
    genesis_acct = genesis.get("account_data", {})
    xrpl_root = results.get("account_info-xrpl-root", {}).get("result", {})
    acct_objs = results.get("account_objects-genesis", {}).get("result", {})
    obj_types = {}
    for o in acct_objs.get("account_objects", []) or []:
        t = o.get("LedgerEntryType", "?")
        obj_types[t] = obj_types.get(t, 0) + 1
    bridge_entry = results.get("ledger_entry-bridge-genesis", {}).get(
        "result", {})

    summary = {
        "probed_at_utc": utcnow(),
        "rpc_calls": calls,
        "rpc_endpoint": RPC,
        "build_version": info.get("build_version"),
        "network_id": info.get("network_id"),
        "validated_ledger_seq": info.get("validated_ledger", {}).get("seq"),
        "validated_ledger_age": info.get("validated_ledger", {}).get("age"),
        "complete_ledgers": info.get("complete_ledgers"),
        "peers": info.get("peers"),
        "validation_quorum": info.get("validation_quorum"),
        "load_factor": info.get("load_factor"),
        "io_latency_ms": info.get("io_latency_ms"),
        "peer_disconnects": info.get("peer_disconnects"),
        "server_state": info.get("server_state"),
        "hostid": info.get("hostid"),
        "ledger_current_index": vl_seq,
        "cadence": cadence,
        "feature_enabled": sum(1 for v in feat.values() if v.get("enabled")),
        "feature_entries": len(feat),
        "xchain_amendments": xchain,
        "genesis_account": {
            "account": GENESIS,
            "exists": bool(genesis_acct),
            "balance_drops": genesis_acct.get("Balance"),
            "flags": genesis_acct.get("Flags"),
            "sequence": genesis_acct.get("Sequence"),
        },
        "xrpl_root_account": {
            "account": XRPL_ROOT,
            "exists": bool(xrpl_root.get("account_data")),
            "error": xrpl_root.get("error"),
            "error_code": xrpl_root.get("error_code"),
        },
        "genesis_account_objects": {
            "count": len(acct_objs.get("account_objects", []) or []),
            "types": obj_types,
            "ledger_index": acct_objs.get("ledger_index"),
        },
        "fabricated_bridge_ledger_entry": {
            "error": bridge_entry.get("error"),
            "error_code": bridge_entry.get("error_code"),
        },
        "validator_list": vl_info,
        "vhs_amendments_info": vhs_info,
        "pfusdc_page": pfusdc_info,
        "explorer": explorer,
    }
    with open(os.path.join(outdir, "derived", "probe-summary.json"), "w") as f:
        json.dump(summary, f, indent=1, sort_keys=True)
    log(f"probe summary written: {json.dumps(summary, sort_keys=True)}")
    log(f"probe end — {calls} HTTP calls total (RPC + GETs)")

    with open(os.path.join(outdir, "probe-run.log"), "w") as f:
        f.write("\n".join(log_lines) + "\n")
        for name in sorted(os.listdir(outdir)):
            if name.endswith(".json"):
                f.write(f"  sha256 {sha256_file(os.path.join(outdir, name))}  {name}\n")


if __name__ == "__main__":
    main()
