#!/usr/bin/env bash
# =====================================================================
# Scheme Sathi — put the code on the VM and start it
# =====================================================================
# Usage:  ./install-on-vm.sh ubuntu@<ip>        # AWS
#         ./install-on-vm.sh azureuser@<ip>     # Azure
#
# Re-runnable. Running it again is how you deploy an update: it re-syncs
# the code, keeps the database and the secrets, and restarts the service.
#
# ! The bot has zero third-party dependencies, so there is no pip step and
# ! nothing to resolve on deploy day. Ubuntu 24.04 ships Python 3.12.
set -euo pipefail

TARGET="${1:?usage: install-on-vm.sh user@host}"
KEY="${KEY:-$([[ -f "$HOME/.ssh/sathi_aws" ]] && echo "$HOME/.ssh/sathi_aws" || echo "$HOME/.ssh/sathi_azure")}"
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
if command -v rsync >/dev/null 2>&1; then
  rsync -az --delete -e "ssh -i $KEY" \
    --exclude '.git' --exclude '.env' --exclude 'sathi.db' \
    --exclude '__pycache__' --exclude '*.pyc' \
    "$SRC/sathi" "$SRC/data" "$SRC/tests" "$SRC/check.py" "$SRC/pyproject.toml" \
    "$TARGET:/tmp/sathi-stage/"
else
  # * Git for Windows ships tar but not rsync. The fixed staging paths keep
  # * this equivalent to rsync --delete without adding another dependency.
  "${SSH[@]}" 'rm -rf /tmp/sathi-stage/sathi /tmp/sathi-stage/data /tmp/sathi-stage/tests /tmp/sathi-stage/check.py /tmp/sathi-stage/pyproject.toml'
  tar -C "$SRC" --exclude='*/__pycache__/*' --exclude='*.pyc' \
    -czf - sathi data tests check.py pyproject.toml \
    | "${SSH[@]}" 'tar -xzf - -C /tmp/sathi-stage'
fi

echo "==> installing secrets (mode 0600, root-owned)"
# ! DB_PATH is rewritten: the laptop's path does not exist on the VM, and the
# ! event log must land on the persistent disk, not in /tmp.
scp -i "$KEY" "$SRC/.env" "$TARGET:/tmp/sathi-stage/sathi.env"

echo "==> installing the unit file"
scp -i "$KEY" "$SRC/deploy/sathi.service" "$TARGET:/tmp/sathi-stage/sathi.service"

echo "==> moving into place, running the checks, starting"
"${SSH[@]}" 'sudo bash -s' <<'REMOTE'
set -euo pipefail

# ! The gate runs on the STAGED copy, before anything live changes. It used to
# ! run after the rsync below: a failing build stopped this script but was
# ! already sitting in /opt/sathi, and the next crash or reboot (every unit is
# ! Restart=always) would have served it to workers. Now a red check.py leaves
# ! /opt/sathi exactly as it was. (AUDIT.md M5)
cd /tmp/sathi-stage && python3 check.py

rsync -a --delete --exclude '__pycache__' \
  /tmp/sathi-stage/{sathi,data,tests,check.py,pyproject.toml} /opt/sathi/
chown -R sathi:sathi /opt/sathi

# ! MERGE the laptop's .env into the server's, never replace it. The laptop
# ! file sets what it sets, but the server also carries settings added there
# ! by hand — PACK_BASE_URL and BOT_URL (RUNBOOK.md), anything else later —
# ! and the REACH_HMAC_KEY that hashes every reach row. Replacing the file
# ! wholesale silently switched pack links and /stats.json off on any deploy
# ! from a laptop whose .env lacked them (found 2026-09-25).
# !   - every KEY= the laptop sets wins, except REACH_HMAC_KEY;
# !   - every KEY= only the server has is carried over, and named below;
# !   - the server's REACH_HMAC_KEY always wins: a new key would count every
# !     existing chat a second time.
merged=/tmp/sathi-stage/sathi.env.merged
# * Strip CR too: a .env saved on Windows would put "\r" at the end of every value.
sed -E -e 's/\r$//' -e 's#^DB_PATH=.*#DB_PATH=/var/lib/sathi/sathi.db#' \
  /tmp/sathi-stage/sathi.env > "$merged"
[[ -s "$merged" && -n "$(tail -c1 "$merged")" ]] && echo >> "$merged"
if [[ -f /etc/sathi/sathi.env ]]; then
  if grep -q '^REACH_HMAC_KEY=' /etc/sathi/sathi.env; then
    sed -i '/^REACH_HMAC_KEY=/d' "$merged"
  fi
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)= ]] || continue
    key="${BASH_REMATCH[1]}"
    if ! grep -q "^${key}=" "$merged"; then
      printf '%s\n' "$line" >> "$merged"
      echo "    kept from the server: $key"
    fi
  done < /etc/sathi/sathi.env
fi
install -m 600 "$merged" /etc/sathi/sathi.env
rm -f "$merged"

cd /opt/sathi

# ! Preserve the old key when upgrading: changing it would count existing
# ! chats again. A new host gets a random key before the service starts.
python3 -m sathi.metrics.events --migrate-reach-key /etc/sathi/sathi.env \
  --db /var/lib/sathi/sathi.db
if ! grep -q '^REACH_HMAC_KEY=' /etc/sathi/sathi.env; then
  printf '\nREACH_HMAC_KEY=%s\n' "$(python3 -c 'import secrets; print(secrets.token_hex(32))')" \
    >> /etc/sathi/sathi.env
  chmod 600 /etc/sathi/sathi.env
fi
chown sathi:sathi /var/lib/sathi/sathi.db

install -m 644 /tmp/sathi-stage/sathi.service /etc/systemd/system/sathi.service
systemctl daemon-reload
systemctl enable sathi
# ! Every enabled Sathi unit, together. They share /opt/sathi and one database;
# ! restarting only `sathi` left whatsapp and web on the previous code.
UNITS="sathi $(systemctl list-unit-files 'sathi-*.service' --state=enabled --no-legend | awk '{print $1}')"
systemctl restart $UNITS
sleep 3
systemctl --no-pager --lines=15 status $UNITS
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
