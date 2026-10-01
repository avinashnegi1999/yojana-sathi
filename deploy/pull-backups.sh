#!/usr/bin/env bash
# =====================================================================
# Scheme Sathi — copy the server's nightly backups to this computer
# =====================================================================
# Usage:  ./deploy/pull-backups.sh ubuntu@<ip> [local folder]
#
# ! This is the off-server copy. The server keeps its last 14 nights in
# ! /var/lib/sathi/backups; one disk failure takes those with it. Run this
# ! from the repo root (it checks the newest copy with sathi.metrics.backup).
# ! Keep the folder private: it holds what the database holds — coarse bands
# ! under random session ids and keyed hashes, never names or phone numbers.
set -euo pipefail

TARGET="${1:?usage: pull-backups.sh user@host [local folder]}"
DEST="${2:-$HOME/sathi-backups}"
KEY="${KEY:-$HOME/.ssh/sathi_aws}"
# ! On Windows, `python3` can be the Microsoft Store stub, which prints an
# ! install hint instead of running. Use the first one that actually runs.
if [[ -z "${PYTHON:-}" ]]; then
  for candidate in python3 python; do
    if "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 11))' 2>/dev/null; then
      PYTHON="$candidate"
      break
    fi
  done
fi
[[ -n "${PYTHON:-}" ]] || { echo "no working Python 3.11+ found; set PYTHON=..."; exit 1; }

mkdir -p "$DEST"
chmod 700 "$DEST"
echo "==> copying /var/lib/sathi/backups from $TARGET to $DEST"
# * The copies are owner-only for the sathi user, so read them with sudo on
# * the server and stream them here; nothing is written on the server.
ssh -i "$KEY" "$TARGET" 'sudo tar -C /var/lib/sathi/backups -cf - .' | tar -C "$DEST" -xf -

newest="$(ls -1 "$DEST"/sathi-*.db 2>/dev/null | tail -1)"
[[ -n "$newest" ]] || { echo "no backups on the server yet"; exit 1; }
echo "==> checking that the newest copy restores"
"$PYTHON" -m sathi.metrics.backup --check "$newest"
