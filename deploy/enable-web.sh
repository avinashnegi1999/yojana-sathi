#!/usr/bin/env bash
# Enable the browser channel on the live host. Run ON the server as root:
#   sudo bash /tmp/enable-web.sh
# Idempotent: re-running changes nothing that is already in place.
#
# ! Exists because the same steps typed from PowerShell lose their inner
# ! double quotes before ssh ever sees them, so the Caddy block arrived
# ! mangled and the unit was never enabled. A file has no quoting problem.
set -euo pipefail

HOST="sathi.avinashnegi.com"
UNIT="/etc/systemd/system/sathi-web.service"
CADDYFILE="/etc/caddy/Caddyfile"

echo "==> unit"
install -m 644 /tmp/sathi-web.service "$UNIT"
systemctl daemon-reload
systemctl enable --now sathi-web
systemctl restart sathi-whatsapp   # * install-on-vm.sh restarts only sathi

echo "==> caddy"
if ! grep -q "^$HOST" "$CADDYFILE"; then
  printf '\n%s {\n    log\n    reverse_proxy 127.0.0.1:8765\n}\n' "$HOST" >> "$CADDYFILE"
fi
caddy validate --config "$CADDYFILE"
systemctl reload caddy

echo "==> status"
systemctl is-active sathi sathi-whatsapp sathi-web caddy
sleep 8
journalctl -u caddy --since '-2min' --no-pager | grep -i "$HOST" | tail -5 || true
echo "Now open https://$HOST"
