#!/usr/bin/env bash
# make_sha256sums.sh — regenerate SHA256SUMS over every file in the pack
# except PACK-READY.md (internal-only) and SHA256SUMS itself.
# Run from the pack root, AFTER the fresh-clone reproduction outputs exist.
set -euo pipefail
cd "$(dirname "$0")/.."
find . -type f \
  ! -name SHA256SUMS ! -name PACK-READY.md \
  ! -path "./.git/*" \
  | LC_ALL=C sort | xargs sha256sum > SHA256SUMS
echo "wrote SHA256SUMS: $(wc -l < SHA256SUMS) files"
