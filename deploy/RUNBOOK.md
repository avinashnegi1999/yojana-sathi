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

## WhatsApp — a second channel, a second unit

The Telegram bot needs no inbound port. The WhatsApp one does, because Meta
pushes webhooks instead of letting us poll. Nothing about the Telegram deploy
changes; `sathi-whatsapp.service` runs beside `sathi.service`.

**Start the paperwork before the deploy.** Meta business verification takes days
to weeks, can fail, and needs a phone number that is not already on WhatsApp. It
runs asynchronously, so begin it first and read the rest of this while it sits in
a queue. Nothing below can be tested without it.

Four secrets go into `/etc/sathi/sathi.env` (mode 0600, owned by `sathi`):

    WHATSAPP_TOKEN=            # System User token, NOT the 24-hour test token
    WHATSAPP_PHONE_NUMBER_ID=
    WHATSAPP_APP_SECRET=       # signs every webhook; the adapter refuses to start without it
    WHATSAPP_VERIFY_TOKEN=     # any string you choose; Meta echoes it back once

### TLS, which the webhook cannot do without

Meta will only call an HTTPS URL with a certificate it trusts, so the adapter
serves plain HTTP on `127.0.0.1:8080` and something in front holds the
certificate. Caddy is the smallest thing that does this correctly — one line of
config and it renews on its own:

    sudo apt install -y caddy
    # /etc/caddy/Caddyfile
    13.206.84.69.nip.io {
        reverse_proxy 127.0.0.1:8080
    }
    sudo systemctl restart caddy

`nip.io` resolves `<ip>.nip.io` to that IP, which is how this gets a real
certificate without buying a domain — Let's Encrypt will not issue one for a bare
IP address.

**Done, 10 Sep 2026.** `yojanasathi.avinashnegi.com` (A record at Spaceship, the
registrar for `avinashnegi.com`) now serves the same adapter, with its own
Let's Encrypt certificate. The Caddyfile lists both names on one site block:

    13.206.84.69.nip.io, yojanasathi.avinashnegi.com {
        log
        reverse_proxy 127.0.0.1:8080
    }

`nip.io` stays because Meta's webhook callback URL points at it, and changing
that URL means re-verifying in the Meta dashboard. The new name is for the
result links a worker taps.

### The pack link route

`/p/*` is served by the **Telegram** process, not the WhatsApp one. That is not
arbitrary: the pack store is a dict in memory, so only the process that
published a pack can serve it. Two copies would answer `410` for half the links.

    yojanasathi.avinashnegi.com {
        log
        handle /p/* {
            reverse_proxy 127.0.0.1:8081
        }
        handle {
            reverse_proxy 127.0.0.1:8080
        }
    }

`sathi.service` needs two variables in `/etc/sathi/sathi.env`:

    PACK_BASE_URL=https://yojanasathi.avinashnegi.com
    BOT_URL=https://t.me/YojanaSathiBot

`PACK_BASE_URL` unset means links are off and the bot sends only the file —
which is what a laptop should do, since a laptop has no reachable host.

### The reach HMAC key

The `reach` table stores `HMAC(key, channel_id)` — never the id itself. That
hash protects an identity only while the key is secret, and a WhatsApp channel
id is a phone number: the space of Indian mobile numbers is around 10^9, small
enough to enumerate. **A key stored in the same SQLite file as the hashes hands
both halves to anyone who obtains one backup.**

Move it out once, per host:

    sudo -u sathi python3 -m sathi.metrics.events         --migrate-reach-key /etc/sathi/sathi.env         --db /var/lib/sathi/sathi.db
    sudo systemctl restart sathi

It moves the **existing value** rather than generating a new one, on purpose: a
fresh key would orphan every reach row, so the next message from someone already
counted would insert a second row and the unique-people number would silently
inflate. It prints a status line and never the key, so the value cannot reach a
terminal scrollback or a shell history. It refuses if the env file already sets
`REACH_HMAC_KEY`, and refuses without deleting anything.

Back up `/etc/sathi/sathi.env` from now on. Losing the key does not lose the
event log, but every future hash stops matching the old rows, so the unique
count restarts.

Two things this exposed, both worth knowing:

- The SSH host key had to be verified before any of this, and the instance's
  boot log no longer carried the fingerprint block — it had been rebooted. The
  fingerprint came from **EC2 Instance Connect** instead (`ssh-keygen -lf
  /etc/ssh/ssh_host_ed25519_key.pub`), which is still AWS's own channel:
  `SHA256:YcS3AZL/KS6+aZ+PY8BAdCdP7fvWpjSidak+8FiqBZk`.
- A crawler hit the new hostname **five seconds** after the certificate was
  issued. Certificate Transparency publishes every hostname in every
  certificate, publicly, immediately. Nothing here is secret, but do not ever
  assume a subdomain is unlisted because you have not shared it.

Then open 443, which the security group currently does not:

    aws ec2 authorize-security-group-ingress --group-name sathi-sg \
        --protocol tcp --port 443 --cidr 0.0.0.0/0

Port 8080 stays closed to the internet. The adapter binds loopback
(`WHATSAPP_BIND`) so an unencrypted copy of the endpoint is never published
beside the encrypted one.

### Wire it up

    sudo cp deploy/sathi-whatsapp.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable --now sathi-whatsapp

In the Meta dashboard → WhatsApp → Configuration, set the callback URL to
`https://13.206.84.69.nip.io/` and the verify token to `WHATSAPP_VERIFY_TOKEN`,
then subscribe to the **messages** field. Saving it triggers one GET, which the
adapter answers with the challenge.

### Verify a deploy actually worked

    # the handshake, from your laptop — 200 and the challenge echoed back
    curl -i "https://13.206.84.69.nip.io/?hub.mode=subscribe&hub.challenge=42&hub.verify_token=$WHATSAPP_VERIFY_TOKEN"

    # a forged webhook must be refused: 403, and nothing in the journal
    curl -i -X POST -d '{}' https://13.206.84.69.nip.io/

    journalctl -u sathi-whatsapp -f     # "listening on 127.0.0.1:8080"

A real message from a real phone is the only end-to-end proof. Nothing before
that shows what the buttons look like on a worker's screen.

### What differs from Telegram, in use

- **Three buttons per message.** Longer question screens become a list behind a
  "Choose" button — one extra tap on occupation, income, land, family size,
  known schemes and documents.
- **`/clear` and `/clearall` cannot work.** The Cloud API has no delete endpoint
  at all, so the bot says so and tells the worker to delete the chat themselves.
  On Telegram both commands still do what they always did.
- **The application pack arrives as `.txt`, not `.html`.** WhatsApp refuses HTML
  documents; the pack is flattened to text and nothing in it is lost, but it no
  longer prints as a page.
- **Voice notes need a supported format.** `.wav` is not one. Point `TTS_CMD` at
  something writing `.ogg` (opus) or `.mp3`, or WhatsApp gets text only.
- **The 24-hour window.** Replies to a worker who wrote first are free and
  unrestricted. That covers the whole screening; only the unbuilt follow-up
  sender would need pre-approved templates.

## Rollback

There is no build artifact to roll back to — the code is the repo. Check out the
last good commit and re-run `install-on-vm.sh`. The database is untouched by a
deploy, so a rollback never loses event history.

## What this deliberately does not have

No Docker, and no reverse proxy, TLS or inbound port on the Telegram side — long
polling makes all of those unnecessary there, and that is still the channel to
reach for first when something has to work today. The WhatsApp unit needs the
proxy and the port because Meta pushes rather than lets us poll; it is additive
and cannot take the Telegram bot down with it. Add Docker when something needs a
dependency.
