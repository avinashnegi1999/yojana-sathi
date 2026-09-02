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

## On Azure

```
az login                       # you, in a browser
./deploy/provision-azure.sh    # once — resource group, B1s VM, SSH lock, budget
./deploy/install-on-vm.sh azureuser@<ip>
```

`install-on-vm.sh` is re-runnable. Running it again **is** the update path: it
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
| `ssh: connection timed out` | your home IP rotated; the NSG still allows the old one | `az network nsg rule update -g scheme-sathi-rg --nsg-name <nsg> -n default-allow-ssh --source-address-prefixes "$(curl -s https://api.ipify.org)"` |
| Bot answers twice, or drops half the messages | two instances on one token | stop the laptop one: `systemctl --user disable --now sathi` |
| `status=203/EXEC` | `/usr/bin/python3` missing | `sudo apt install -y python3` |
| Restart loop every 10s | bad `/etc/sathi/sathi.env` | `sudo cat /etc/sathi/sathi.env` — check `TELEGRAM_TOKEN` |
| Bot silently dead, VM gone | student credit exhausted | portal > Cost Management. The $60 budget alert exists to prevent this |
| Impact numbers reset to zero | `DB_PATH` not on the persistent disk | must be `/var/lib/sathi/sathi.db`, never `/tmp` |

## Rollback

There is no build artifact to roll back to — the code is the repo. Check out the
last good commit and re-run `install-on-vm.sh`. The database is untouched by a
deploy, so a rollback never loses event history.

## What this deliberately does not have

No reverse proxy, no TLS, no inbound port, no Docker, no CI. Long polling makes
all four unnecessary. Add CI when a second person can deploy; add Docker when
something needs a dependency.
