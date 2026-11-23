#!/usr/bin/env bash
# verify_digests.sh — verify SHA256SUMS against the pack as shipped.
# Run from the pack root. Exit 0 only if every file verifies.
set -euo pipefail
cd "$(dirname "$0")/.."
sha256sum -c SHA256SUMS
