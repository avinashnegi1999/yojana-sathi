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
# * A unit that crash-looped earlier (code not yet synced) trips systemd's
# * start limit and stays "failed" until told otherwise.
systemctl reset-failed sathi-web 2>/dev/null || true
systemctl enable sathi-web
systemctl restart sathi-web
systemctl restart sathi-whatsapp   # * install-on-vm.sh restarts only sathi

echo "==> caddy"
# ! Redacted access log, the same shape as the pack host in RUNBOOK.md. The
# ! plain `log` this used to write recorded every worker's IP, phone model and
# ! the full /document/<token> URL — a bearer link to her sheet — for every
# ! request (reproduced on Caddy 2.6.2 and 2.11.4; AUDIT.md M8).
if ! grep -q "^$HOST" "$CADDYFILE"; then
  cat >> "$CADDYFILE" <<CADDY

$HOST {
    log {
        format filter {
            wrap console
            fields {
                request>uri regexp "/document/[^\s?#]+" "/document/REDACTED"
                request>remote_ip delete
                request>remote_port delete
                request>client_ip delete
                request>headers>User-Agent delete
                request>headers>X-Forwarded-For delete
            }
        }
    }
    reverse_proxy 127.0.0.1:8765
}
CADDY
elif ! grep -q "/document/REDACTED" "$CADDYFILE"; then
  # ! An older run of this script already wrote a plain `log` block. It is
  # ! not safe to rewrite someone's Caddyfile with sed, so stop and say so.
  echo "!! $CADDYFILE has a $HOST block without log redaction."
  echo "!! Replace its 'log' line with the block in deploy/RUNBOOK.md"
  echo "!! (section: The browser channel), then run: sudo systemctl reload caddy"
  exit 1
fi
caddy validate --config "$CADDYFILE"
systemctl reload caddy

echo "==> status"
systemctl is-active sathi sathi-whatsapp sathi-web caddy
sleep 8
journalctl -u caddy --since '-2min' --no-pager | grep -i "$HOST" | tail -5 || true
echo "Now open https://$HOST"
