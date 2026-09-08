#!/usr/bin/env bash
# =====================================================================
# Scheme Sathi — create the Azure VM that runs the bot
# =====================================================================
# Run this ONCE, from the laptop, after `az login`.
# It creates: a resource group, a B1s Ubuntu VM, an SSH key, and a budget
# alert. It does NOT deploy the code — that is install-on-vm.sh, run second.
#
# ! Nothing here opens an inbound port except SSH, and SSH is locked to your
# ! current public IP. The bot uses Telegram long polling: outbound only.
set -euo pipefail

RG="${RG:-scheme-sathi-rg}"
LOCATION="${LOCATION:-centralindia}"
VM="${VM:-sathi-vm}"
# * B1s: 1 vCPU / 1 GB. The bot is stdlib Python holding one HTTP connection
# * and a SQLite file. ~$8/month, so the $100 student credit lasts ~10 months
# * against a hackathon that ends in December.
SIZE="${SIZE:-Standard_B1s}"
ADMIN="${ADMIN:-azureuser}"
KEY="${KEY:-$HOME/.ssh/sathi_azure}"

echo "==> subscription"
az account show --query "{name:name, state:state, id:id}" -o table

# ! Confirm this is the student subscription before spending anything.
read -rp "Is the subscription above the Azure for Students one? [y/N] " ok
[[ "$ok" == "y" || "$ok" == "Y" ]] || { echo "Pick it with: az account set --subscription <id>"; exit 1; }

echo "==> ssh key"
if [[ ! -f "$KEY" ]]; then
  ssh-keygen -t ed25519 -f "$KEY" -N "" -C "sathi-azure"
  echo "created $KEY"
else
  echo "reusing $KEY"
fi

echo "==> resource group"
az group create --name "$RG" --location "$LOCATION" -o none

echo "==> your public IP (to lock SSH to)"
MYIP="$(curl -fsS https://api.ipify.org)"
echo "    $MYIP"

echo "==> vm (this takes 1-2 minutes)"
az vm create \
  --resource-group "$RG" \
  --name "$VM" \
  --image Ubuntu2404 \
  --size "$SIZE" \
  --admin-username "$ADMIN" \
  --ssh-key-values "${KEY}.pub" \
  --public-ip-sku Standard \
  --storage-sku StandardSSD_LRS \
  --os-disk-size-gb 30 \
  --nsg-rule SSH \
  -o none

echo "==> lock SSH to your IP only"
NSG="$(az network nsg list -g "$RG" --query "[0].name" -o tsv)"
az network nsg rule update -g "$RG" --nsg-name "$NSG" -n default-allow-ssh \
  --source-address-prefixes "$MYIP" -o none

# ! Home IPs rotate. If ssh stops working later, this is why — rerun:
# !   az network nsg rule update -g RG --nsg-name NSG -n default-allow-ssh \
# !     --source-address-prefixes "$(curl -s https://api.ipify.org)"

IP="$(az vm show -d -g "$RG" -n "$VM" --query publicIps -o tsv)"

echo "==> budget alert at \$60 of the \$100 credit"
SUB="$(az account show --query id -o tsv)"
# ! The student credit hard-stops at \$100 with no bill, which is safe but
# ! silent — the bot would just die. This mails a warning with room to react.
EMAIL="$(az account show --query user.name -o tsv)"
az consumption budget create \
  --budget-name sathi-credit-warning \
  --amount 60 \
  --category Cost \
  --time-grain Monthly \
  --start-date "$(date -u +%Y-%m-01)" \
  --end-date "$(date -u -d '+11 months' +%Y-%m-01)" \
  -o none 2>/dev/null \
  && echo "    budget created (check alert email $EMAIL in the portal)" \
  || echo "    ! budget API refused — set it by hand: portal > Cost Management > Budgets"

cat <<EOF

=====================================================================
VM is up.

  ssh -i $KEY $ADMIN@$IP

Next:  ./install-on-vm.sh $ADMIN@$IP
=====================================================================
EOF
