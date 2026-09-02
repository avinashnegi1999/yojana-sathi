#!/usr/bin/env bash
# =====================================================================
# Scheme Sathi — put the code on the VM and start it
# =====================================================================
# Usage:  ./install-on-vm.sh azureuser@<ip>
#
# Re-runnable. Running it again is how you deploy an update: it re-syncs
# the code, keeps the database and the secrets, and restarts the service.
#
# ! The bot has zero third-party dependencies, so there is no pip step and
# ! nothing to resolve on deploy day. Ubuntu 24.04 ships Python 3.12.
set -euo pipefail

TARGET="${1:?usage: install-on-vm.sh user@host}"
KEY="${KEY:-$HOME/.ssh/sathi_azure}"
SRC="$(cd "$(dirname "$0")/.." && pwd)"
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$TARGET")

[[ -f "$SRC/.env" ]] || { echo "no .env at $SRC — cannot deploy without TELEGRAM_TOKEN"; exit 1; }

echo "==> creating the sathi user and directories"
"${SSH[@]}" 'sudo bash -s' <<'REMOTE'
set -euo pipefail
id -u sathi &>/dev/null || useradd --system --home /opt/sathi --shell /usr/sbin/nologin sathi
mkdir -p /opt/sathi /var/lib/sathi /etc/sathi /tmp/sathi-stage
chown -R sathi:sathi /opt/sathi /var/lib/sathi
chmod 700 /etc/sathi
chown "$SUDO_USER":"$SUDO_USER" /tmp/sathi-stage
REMOTE

echo "==> syncing code (no .env, no local database, no git history)"
# ! sathi.db is excluded deliberately. The VM keeps its own event log; copying
# ! the laptop's test database over it would put fake sessions in the impact
# ! numbers, and those numbers are 25% of the hackathon score.
rsync -az --delete -e "ssh -i $KEY" \
  --exclude '.git' --exclude '.env' --exclude 'sathi.db' \
  --exclude '__pycache__' --exclude '*.pyc' \
  "$SRC/sathi" "$SRC/data" "$SRC/tests" "$SRC/check.py" "$SRC/pyproject.toml" \
  "$TARGET:/tmp/sathi-stage/"

echo "==> installing secrets (mode 0600, root-owned)"
# ! DB_PATH is rewritten: the laptop's path does not exist on the VM, and the
# ! event log must land on the persistent disk, not in /tmp.
sed -E 's#^DB_PATH=.*#DB_PATH=/var/lib/sathi/sathi.db#' "$SRC/.env" \
  | "${SSH[@]}" 'sudo tee /etc/sathi/sathi.env >/dev/null && sudo chmod 600 /etc/sathi/sathi.env'

echo "==> installing the unit file"
scp -i "$KEY" "$SRC/deploy/sathi.service" "$TARGET:/tmp/sathi-stage/sathi.service"

echo "==> moving into place, running the checks, starting"
"${SSH[@]}" 'sudo bash -s' <<'REMOTE'
set -euo pipefail
rsync -a --delete /tmp/sathi-stage/{sathi,data,tests,check.py,pyproject.toml} /opt/sathi/
chown -R sathi:sathi /opt/sathi

# ! The same check.py that gates the Docker build gates the deploy. A VM that
# ! cannot pass its own tests must not talk to a worker.
cd /opt/sathi && python3 check.py

install -m 644 /tmp/sathi-stage/sathi.service /etc/systemd/system/sathi.service
systemctl daemon-reload
systemctl enable sathi
systemctl restart sathi
sleep 3
systemctl --no-pager --lines=15 status sathi
REMOTE

cat <<EOF

=====================================================================
Deployed. It survives reboots.

  logs      ssh -i $KEY $TARGET 'journalctl -u sathi -f'
  restart   ssh -i $KEY $TARGET 'sudo systemctl restart sathi'
  update    ./install-on-vm.sh $TARGET

Now message @YojanaSathiBot and confirm it answers.
=====================================================================
EOF
