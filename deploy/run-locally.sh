#!/usr/bin/env bash
# =====================================================================
# Scheme Sathi — run it on THIS machine as a service
# =====================================================================
# For starting the usage clock today, before the VM exists. Uses a --user
# systemd service, so no root and no password.
#
# ! Same code, same unit shape as the VM. Moving to Azure later changes the
# ! host and nothing else.
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
UNIT="$HOME/.config/systemd/user/sathi.service"

mkdir -p "$(dirname "$UNIT")"
sed -e '/^User=/d' -e '/^Group=/d' \
    -e '/^Protect/d' -e '/^ReadWritePaths=/d' -e '/^Restrict/d' \
    -e '/^NoNewPrivileges=/d' -e '/^PrivateTmp=/d' \
    -e '/^LockPersonality=/d' -e '/^MemoryDenyWriteExecute=/d' \
    -e "s#^WorkingDirectory=.*#WorkingDirectory=$SRC#" \
    -e "s#^EnvironmentFile=.*#EnvironmentFile=$SRC/.env#" \
    -e 's#^ExecStart=.*#ExecStart=/usr/bin/python3 -m sathi.main --telegram#' \
    -e 's#^WantedBy=.*#WantedBy=default.target#' \
    "$SRC/deploy/sathi.service" > "$UNIT"

systemctl --user daemon-reload
systemctl --user enable sathi
# ! `enable --now` only STARTS a stopped service — re-running this script on a
# ! live bot left the old process up with the old unit, so an edit here looked
# ! applied and was not. This script is the update path, so it must restart.
systemctl --user restart sathi

# ! Without lingering the service dies at logout. This is the whole point of
# ! running it as a service rather than in a terminal.
loginctl enable-linger "$USER" 2>/dev/null || \
  echo "! could not enable linger — run: sudo loginctl enable-linger $USER"

sleep 2
systemctl --user --no-pager --lines=15 status sathi
echo
echo "logs: journalctl --user -u sathi -f"
echo "stop: systemctl --user disable --now sathi"
