# Deploy runbook

Three scripts. The unit file is the same everywhere, so moving hosts is a
change of address and nothing else.

## Today, before Azure exists — start the usage clock

```
./deploy/run-locally.sh
```

Runs the bot as a `--user` systemd service on this laptop with lingering on, so
it survives logout. It still dies when the machine is off; that is the only
reason to move to a VM.

## On AWS — the live host

```
~/.local/bin/aws configure     # once — key, secret, region ap-south-1
./deploy/provision-aws.sh      # once — ssh key, security group, t4g.micro, budget
KEY=~/.ssh/sathi_aws ./deploy/install-on-vm.sh ubuntu@<ip>
```

`provision-aws.sh` is safe to re-run: it finds an existing `sathi-vm` and prints
its address instead of launching a second one that would fight the first for the
bot token.

Cost, ap-south-1: `t4g.micro` ~$6.10/mo + 8GB gp3 ~$0.73 + public IPv4 ~$3.65 =
**~$10.50/mo**. The Free Plan credit is $120, but the plan itself expires six
months after signup — that, not the balance, is the real deadline.

## On Azure — not provisioned, kept for reference

Blocked on academic verification: `az login` works but returns no subscription.

```
az login                       # you, in a browser
./deploy/provision-azure.sh    # once — resource group, B1s VM, SSH lock, budget
./deploy/install-on-vm.sh azureuser@<ip>
```

`install-on-vm.sh` is host-agnostic and re-runnable — it picks `sathi_aws` as
the key when that file exists. Running it again **is** the update path: it
re-syncs code, keeps `/var/lib/sathi/sathi.db` and `/etc/sathi/sathi.env`, runs
`check.py` on the VM, and restarts.

Stop the local service first — **two copies long-polling the same bot token
will steal updates from each other** and roughly half of every conversation
will vanish:

```
systemctl --user disable --now sathi
```

## Verify a deploy actually worked

1. `journalctl -u sathi -n 50` — no traceback, no restart loop.
2. Message @YojanaSathiBot `/start` and walk one full screening.
3. `sudo ls -la /var/lib/sathi/sathi.db` — file exists and grew.
4. `sudo systemctl reboot`, wait, message it again. If it answers, persistence
   and restart-on-boot are both real. Do this once, on deploy day, not later.

## When it breaks

| Symptom | Cause | Fix |
|---|---|---|
| `ssh: connection timed out` | your home IP rotated; the security group still allows the old one | AWS: `aws ec2 authorize-security-group-ingress --region ap-south-1 --group-id <sg> --protocol tcp --port 22 --cidr "$(curl -s https://api.ipify.org)/32"` · Azure: `az network nsg rule update -g scheme-sathi-rg --nsg-name <nsg> -n default-allow-ssh --source-address-prefixes "$(curl -s https://api.ipify.org)"` |
| Bot answers twice, or drops half the messages | two instances on one token | stop the laptop one: `systemctl --user disable --now sathi` |
| `status=203/EXEC` | `/usr/bin/python3` missing | `sudo apt install -y python3` |
| Restart loop every 10s | bad `/etc/sathi/sathi.env` | `sudo cat /etc/sathi/sathi.env` — check `TELEGRAM_TOKEN` |
| Bot silently dead, instance gone | credit exhausted or Free Plan expired | AWS: Billing > Budgets — the zero-spend alert fires the day real money starts. Azure: portal > Cost Management |
| Impact numbers reset to zero | `DB_PATH` not on the persistent disk | must be `/var/lib/sathi/sathi.db`, never `/tmp` |

## Rollback

There is no build artifact to roll back to — the code is the repo. Check out the
last good commit and re-run `install-on-vm.sh`. The database is untouched by a
deploy, so a rollback never loses event history.

## What this deliberately does not have

No reverse proxy, no TLS, no inbound port, no Docker, no CI. Long polling makes
all four unnecessary. Add CI when a second person can deploy; add Docker when
something needs a dependency.
