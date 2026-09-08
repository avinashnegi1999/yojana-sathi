#!/usr/bin/env bash
# =====================================================================
# Scheme Sathi — replace WHATSAPP_TOKEN on the VM, and on this machine
# =====================================================================
# Usage:  ./rotate-whatsapp-token.sh ubuntu@<ip>
#
# ! The token is read with `read -s`: never echoed, never passed as an argument
# ! (argv is world-readable in /proc), never written to a temp file, never in
# ! shell history. It moves on stdin only.
#
# ! It updates BOTH the VM's /etc/sathi/sathi.env AND the local .env, because
# ! install-on-vm.sh rebuilds the remote env from the local copy. Update one
# ! and not the other and the next deploy quietly restores the dead token.
set -euo pipefail

TARGET="${1:?usage: rotate-whatsapp-token.sh user@host}"
KEY="${KEY:-$HOME/.ssh/sathi_aws}"
SRC="$(cd "$(dirname "$0")/.." && pwd)"
SSH=(ssh -i "$KEY" -o StrictHostKeyChecking=accept-new "$TARGET")

[[ -f "$SRC/.env" ]] || { echo "no .env at $SRC"; exit 1; }

read -rsp "Paste the System User token (input hidden): " TOKEN
echo
[[ -n "$TOKEN" ]] || { echo "empty token, nothing done"; exit 1; }
# * Meta tokens start EAA. A half-copied paste is the likeliest failure here,
# * and it is cheaper to catch now than after a restart.
[[ "$TOKEN" == EAA* ]] || { echo "does not look like a Meta token (expected EAA...)"; exit 1; }

PHONE_ID="$(grep -E '^WHATSAPP_PHONE_NUMBER_ID=' "$SRC/.env" | cut -d= -f2-)"
[[ -n "$PHONE_ID" ]] || { echo "WHATSAPP_PHONE_NUMBER_ID missing from $SRC/.env"; exit 1; }

echo "==> checking the token against the Graph API before touching anything"
code="$(curl -s -o /dev/null -w '%{http_code}' \
  "https://graph.facebook.com/v21.0/${PHONE_ID}" -H "Authorization: Bearer ${TOKEN}")"
[[ "$code" == "200" ]] || {
  echo "token rejected: HTTP $code — nothing was written."
  echo "check both whatsapp_business_* scopes, and that the WABA was assigned."
  exit 1
}
echo "    ok, HTTP 200"

# ! One rewriter, used locally and remotely. Replaces the WHATSAPP_TOKEN line
# ! and leaves every other line untouched; appends it if the key is absent.
REWRITE='
import pathlib, sys
token = sys.stdin.read().strip()
p = pathlib.Path(sys.argv[1])
out, seen = [], False
for line in p.read_text().splitlines():
    if line.startswith("WHATSAPP_TOKEN="):
        out.append("WHATSAPP_TOKEN=" + token); seen = True
    else:
        out.append(line)
if not seen:
    out.append("WHATSAPP_TOKEN=" + token)
p.write_text("\n".join(out) + "\n")
p.chmod(0o600)
'

echo "==> updating the local .env"
printf '%s' "$TOKEN" | python3 -c "$REWRITE" "$SRC/.env"

echo "==> updating /etc/sathi/sathi.env on the VM"
printf '%s' "$TOKEN" | "${SSH[@]}" "sudo python3 -c '$REWRITE' /etc/sathi/sathi.env"

echo "==> restarting the WhatsApp unit"
"${SSH[@]}" 'sudo systemctl restart sathi-whatsapp && sleep 2 && sudo systemctl is-active sathi-whatsapp'

echo "==> last 15 log lines"
"${SSH[@]}" 'sudo journalctl -u sathi-whatsapp --no-pager --lines=15'

unset TOKEN
echo
echo "done. Telegram was not touched."
