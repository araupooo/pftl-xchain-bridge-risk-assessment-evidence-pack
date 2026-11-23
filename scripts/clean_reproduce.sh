#!/usr/bin/env bash
# clean_reproduce.sh — re-run every measurement fresh and compare with the
# shipped results. Exit 0 only if every check passes.
#
# Run from the pack root. Writes fresh outputs under outputs/fresh-clone/
# (probe outputs, derived tables, drill log) and prints a PASS line per
# check plus the exit code. The fresh run re-probes the live testnet, so
# the validated ledger is expected to have ADVANCED since the shipped
# probe; that advance is itself one of the checks.
#
# The pinned source checkout is taken from $PIN_CHECKOUT (default
# /tmp/postfiatd-pin); if it is absent, postfiatd is cloned and the
# pinned commit is checked out into /tmp/postfiatd-pin-repro.
set -euo pipefail
cd "$(dirname "$0")/.."
# Never write .pyc files into the pack: the bytecode embeds the pack's
# absolute path, which would leak the internal task folder name.
export PYTHONDONTWRITEBYTECODE=1
PIN="${PIN:-0085a1ff885d6a446369cf73a4430f75af22be55}"
PIN_CHECKOUT="${PIN_CHECKOUT:-/tmp/postfiatd-pin}"
FRESH="outputs/fresh-clone"

echo "== clean reproduce =="
echo "pinned commit: $PIN"
if [ -d "$PIN_CHECKOUT/.git" ]; then
  HEAD="$(git -C "$PIN_CHECKOUT" rev-parse HEAD)"
  if [ "$HEAD" != "$PIN" ]; then
    echo "FAIL pinned checkout HEAD is $HEAD, expected $PIN" >&2
    exit 1
  fi
  echo "PASS pinned checkout HEAD verified — $HEAD"
else
  echo "pinned checkout missing at $PIN_CHECKOUT — cloning postfiatd"
  PIN_CHECKOUT="/tmp/postfiatd-pin-repro"
  rm -rf "$PIN_CHECKOUT"
  git clone --quiet https://github.com/postfiatorg/postfiatd.git "$PIN_CHECKOUT"
  git -C "$PIN_CHECKOUT" checkout --quiet "$PIN"
  echo "PASS pinned checkout cloned — $(git -C "$PIN_CHECKOUT" rev-parse HEAD)"
fi

rm -rf "$FRESH"
mkdir -p "$FRESH/derived"
export PIN_CHECKOUT

echo "== excerpts =="
python3 scripts/extract_excerpts.py --pin "$PIN_CHECKOUT" --out "$FRESH/fixtures" >/dev/null
echo "PASS excerpts re-extracted from pinned checkout"

echo "== live probes (includes a 60 s cadence window) =="
python3 scripts/probe_all.py --outdir "$FRESH"

echo "== drills =="
python3 scripts/drill.py --outdir "$FRESH"

echo "== analysis =="
python3 scripts/analyze.py --outdir "$FRESH"

echo "== compare with shipped results =="
python3 scripts/compare_reproduce.py | tee outputs/fresh-clone-compare.log
echo "exit code: ${PIPESTATUS[0]}"
