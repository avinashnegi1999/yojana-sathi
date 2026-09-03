#!/usr/bin/env bash
# =====================================================================
# Scheme Sathi — create the AWS EC2 instance that runs the bot
# =====================================================================
# Run this ONCE, from the laptop, after `aws configure`.
# It creates: an SSH key, a security group locked to your IP, a t4g.micro
# Ubuntu instance, and a zero-spend budget alert. It does NOT deploy the
# code — that is install-on-vm.sh, run second.
#
# ! Nothing here opens an inbound port except SSH, and SSH is locked to your
# ! current public IP. The bot uses Telegram long polling: outbound only.
#
# Re-runnable: if the instance already exists it prints the address and stops
# rather than building a second one that would fight the first for the token.
set -euo pipefail

AWS="${AWS_BIN:-$HOME/.local/bin/aws}"
REGION="${REGION:-ap-south-1}"          # * Mumbai — nearest region to the users
NAME="${NAME:-sathi-vm}"
SG="${SG:-sathi-sg}"
KEYNAME="${KEYNAME:-sathi-aws}"
KEY="${KEY:-$HOME/.ssh/sathi_aws}"
# * t4g.micro: 2 vCPU / 1 GB ARM. The bot is stdlib Python holding one HTTP
# * connection and a SQLite file. ~$6/month + $0.73 disk + $3.65 IPv4, so the
# * $120 credit outlives the 6-month Free Plan it came with.
TYPE="${TYPE:-t4g.micro}"
ARCH="${ARCH:-arm64}"
DISK_GB="${DISK_GB:-8}"
EMAIL="${EMAIL:-}"

export AWS_PAGER=""

echo "==> account"
"$AWS" sts get-caller-identity --output table --region "$REGION"
ACCOUNT="$("$AWS" sts get-caller-identity --query Account --output text --region "$REGION")"

# ! Confirm before spending. A wrong account here bills a card instead of credit.
read -rp "Is the account above the one holding the \$120 credit? [y/N] " ok
[[ "$ok" == "y" || "$ok" == "Y" ]] || { echo "Switch with: $AWS configure"; exit 1; }

echo "==> existing instance?"
EXISTING="$("$AWS" ec2 describe-instances --region "$REGION" \
  --filters "Name=tag:Name,Values=$NAME" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
  --query "Reservations[].Instances[].[InstanceId,State.Name,PublicIpAddress]" --output text)"
if [[ -n "$EXISTING" ]]; then
  echo "    already exists:"
  echo "$EXISTING" | sed 's/^/    /'
  echo
  echo "    Deploy to it:  KEY=$KEY ./deploy/install-on-vm.sh ubuntu@<ip>"
  echo "    Delete it:     $AWS ec2 terminate-instances --region $REGION --instance-ids <id>"
  exit 0
fi

echo "==> ssh key"
if [[ ! -f "$KEY" ]]; then
  ssh-keygen -t ed25519 -f "$KEY" -N "" -C "sathi-aws"
  echo "    created $KEY"
else
  echo "    reusing $KEY"
fi
# ! import-key-pair, not create-key-pair: AWS never sees the private half.
"$AWS" ec2 describe-key-pairs --region "$REGION" --key-names "$KEYNAME" >/dev/null 2>&1 \
  || "$AWS" ec2 import-key-pair --region "$REGION" --key-name "$KEYNAME" \
       --public-key-material "fileb://${KEY}.pub" --output text >/dev/null

echo "==> your public IP (to lock SSH to)"
MYIP="$(curl -fsS https://api.ipify.org)"
echo "    $MYIP"

echo "==> security group"
VPC="$("$AWS" ec2 describe-vpcs --region "$REGION" --filters Name=isDefault,Values=true \
  --query "Vpcs[0].VpcId" --output text)"
[[ "$VPC" != "None" && -n "$VPC" ]] || { echo "no default VPC in $REGION — create one in the console"; exit 1; }

SGID="$("$AWS" ec2 describe-security-groups --region "$REGION" \
  --filters "Name=group-name,Values=$SG" "Name=vpc-id,Values=$VPC" \
  --query "SecurityGroups[0].GroupId" --output text 2>/dev/null || echo None)"
if [[ "$SGID" == "None" || -z "$SGID" ]]; then
  SGID="$("$AWS" ec2 create-security-group --region "$REGION" --group-name "$SG" \
    --description "Scheme Sathi - SSH from one address, nothing else inbound" \
    --vpc-id "$VPC" --query GroupId --output text)"
  echo "    created $SGID"
else
  echo "    reusing $SGID"
fi
# ! Idempotent: a duplicate rule is not an error worth stopping for.
"$AWS" ec2 authorize-security-group-ingress --region "$REGION" --group-id "$SGID" \
  --protocol tcp --port 22 --cidr "${MYIP}/32" --output text >/dev/null 2>&1 \
  && echo "    SSH allowed from ${MYIP}/32" \
  || echo "    SSH rule for ${MYIP}/32 already present"

# ! Home IPs rotate. If ssh stops working later, this is why — rerun:
# !   aws ec2 authorize-security-group-ingress --region REGION --group-id SGID \
# !     --protocol tcp --port 22 --cidr "$(curl -s https://api.ipify.org)/32"

echo "==> latest Ubuntu 24.04 $ARCH image"
# ! Canonical publishes the current AMI id as a public SSM parameter, so this
# ! never pins a stale image the way a hardcoded ami- id would.
AMI="$("$AWS" ssm get-parameters --region "$REGION" \
  --names "/aws/service/canonical/ubuntu/server/24.04/stable/current/${ARCH}/hvm/ebs-gp3/ami-id" \
  --query "Parameters[0].Value" --output text)"
[[ "$AMI" == ami-* ]] || { echo "could not resolve an AMI id (got: $AMI)"; exit 1; }
echo "    $AMI"

echo "==> launching $TYPE (this takes about a minute)"
IID="$("$AWS" ec2 run-instances --region "$REGION" \
  --image-id "$AMI" --instance-type "$TYPE" --key-name "$KEYNAME" \
  --security-group-ids "$SGID" \
  --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=${DISK_GB},VolumeType=gp3,DeleteOnTermination=true,Encrypted=true}" \
  --metadata-options "HttpTokens=required,HttpEndpoint=enabled" \
  --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$NAME}]" \
  --query "Instances[0].InstanceId" --output text)"
echo "    $IID"

"$AWS" ec2 wait instance-running --region "$REGION" --instance-ids "$IID"
IP="$("$AWS" ec2 describe-instances --region "$REGION" --instance-ids "$IID" \
  --query "Reservations[0].Instances[0].PublicIpAddress" --output text)"

echo "==> zero-spend budget alert"
if [[ -z "$EMAIL" ]]; then
  read -rp "    email for the budget alert (blank to skip): " EMAIL
fi
if [[ -z "$EMAIL" ]]; then
  echo "    skipped — set one later: Billing > Budgets"
else
# ! Credits hide the bill until they do not. This stays silent while credit
# ! covers everything and mails the moment real money starts, which is the
# ! day the Free Plan expires under a still-running instance.
BUDGET="$(mktemp)"; NOTIFY="$(mktemp)"
cat > "$BUDGET" <<JSON
{"BudgetName":"sathi-zero-spend","BudgetLimit":{"Amount":"1","Unit":"USD"},
 "TimeUnit":"MONTHLY","BudgetType":"COST"}
JSON
cat > "$NOTIFY" <<JSON
[{"Notification":{"NotificationType":"ACTUAL","ComparisonOperator":"GREATER_THAN",
  "Threshold":1,"ThresholdType":"PERCENTAGE"},
  "Subscribers":[{"SubscriptionType":"EMAIL","Address":"$EMAIL"}]}]
JSON
"$AWS" budgets create-budget --account-id "$ACCOUNT" \
  --budget "file://$BUDGET" --notifications-with-subscribers "file://$NOTIFY" >/dev/null 2>&1 \
  && echo "    budget created — alerts $EMAIL" \
  || echo "    ! budget refused (already exists, or no billing permission) — set it by hand: Billing > Budgets"
rm -f "$BUDGET" "$NOTIFY"
fi

cat <<EOF

=====================================================================
Instance is up.

  ssh -i $KEY ubuntu@$IP

Next:  KEY=$KEY ./deploy/install-on-vm.sh ubuntu@$IP

Then STOP the laptop copy — two pollers on one token steal each other's
updates and half of every conversation vanishes:

  systemctl --user disable --now sathi
=====================================================================
EOF
