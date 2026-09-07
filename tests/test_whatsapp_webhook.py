"""The WhatsApp webhook over a real socket. Run: python3 tests/test_whatsapp_webhook.py

# ! Everything else about this adapter is checked by calling its methods. This
# ! file binds a port and speaks HTTP to it, because the endpoint is the one
# ! part of the project that answers strangers: the signature check, the
# ! verification handshake and the "answer 200 before doing the work" ordering
# ! only exist inside the request handler, and a mocked call never touches them.
"""

import hashlib
import hmac
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sathi.channels import whatsapp
from sathi.channels.whatsapp import WhatsAppBot, _webhook_handler
from sathi.core.schemes import Criterion, Scheme

SECRET = "app-secret"
VERIFY = "verify-token"

SCHEMES = {"A": Scheme(
    code="A", name_en="A", name_hi="योजना-A", authority="x", official_url="u",
    verified_on="2026-09-01", verified_by="a",
    benefit={"annual_value_inr": 1000, "value_basis": "annual_payout", "summary_hi": "प"},
    criteria=(Criterion("age", "between", [18, 40], "u", pass_hi="ok", fail_hi="no"),),
    exclusions=(), documents=("आधार",), where_to_apply="csc", renewal="none",
)}


def _message(body: str, sender: str = "911", wamid: str = "wamid.1") -> dict:
    return {"object": "whatsapp_business_account", "entry": [{"id": "1", "changes": [
        {"field": "messages", "value": {"messaging_product": "whatsapp", "messages": [
            {"id": wamid, "from": sender, "type": "text", "text": {"body": body}},
        ]}},
    ]}]}


def _sign(body: bytes) -> str:
    return "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


def _request(url: str, body: bytes | None = None, signature: str | None = None) -> int:
    headers = {"content-type": "application/json"} if body else {}
    if signature is not None:
        headers["x-hub-signature-256"] = signature
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def run() -> None:
    sent: list[dict] = []
    real_post = whatsapp._post
    whatsapp._post = lambda token, path, payload: (
        sent.append(payload) or {"messages": [{"id": f"wamid.out.{len(sent)}"}]}
    )
    bot = WhatsAppBot(SCHEMES, token="t", phone_number_id="1",
                      app_secret=SECRET, verify_token=VERIFY)
    server = ThreadingHTTPServer(("127.0.0.1", 0), _webhook_handler(bot))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"

    try:
        # ! The verification handshake. Meta calls this once, and so does
        # ! anyone who finds the URL — only the right token gets the challenge.
        status, body = _request(f"{base}/?hub.mode=subscribe&"
                                f"hub.verify_token={VERIFY}&hub.challenge=42")
        assert (status, body) == (200, b"42"), (status, body)
        for query in (f"hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=42",
                      f"hub.mode=subscribe&hub.challenge=42",
                      f"hub.verify_token={VERIFY}&hub.challenge=42"):
            status, _ = _request(f"{base}/?{query}")
            assert status == 403, (query, status)
        print("  ok  test_verification_handshake")

        # ! An unsigned or wrongly signed body is not from Meta. It must be
        # ! refused before it can reach a Conversation.
        payload = json.dumps(_message("/start")).encode()
        for signature in (None, "", "sha256=" + "0" * 64, _sign(payload + b" ")):
            status, _ = _request(base + "/", payload, signature)
            assert status == 403, (signature, status)
        assert bot._work.qsize() == 0, "a forged webhook was queued"
        assert not sent, "a forged webhook reached the wire"
        print("  ok  test_forged_webhooks_are_refused")

        # * Signed but not JSON.
        broken = b"not json"
        status, _ = _request(base + "/", broken, _sign(broken))
        assert status == 400, status

        # ! A signed message is acknowledged BEFORE it is processed. Meta
        # ! redelivers anything it does not see acknowledged in seconds, and
        # ! generating a pack takes longer than that.
        status, _ = _request(base + "/", payload, _sign(payload))
        assert status == 200, status
        # ! The 200 is sent BEFORE the enqueue, deliberately — so the client can
        # ! see the response while the handler thread has not queued yet. Wait
        # ! for the queue rather than sampling it, or this races on a loaded
        # ! machine and fails in CI while passing on a fast laptop.
        deadline = time.monotonic() + 5
        while bot._work.qsize() == 0 and time.monotonic() < deadline:
            time.sleep(0.005)
        assert bot._work.qsize() == 1, "the signed message was never queued"
        # ! This is the real claim: the request thread acknowledged and walked
        # ! away, it did not run the conversation itself.
        assert not bot.sessions, "the request thread ran the conversation itself"

        assert bot.work_once(block=False) is True
        assert "911" in bot.sessions, "the queued message never reached the flow"
        assert "Choose your language" in sent[-1]["interactive"]["body"]["text"]
        assert sent[-1]["to"] == "911"
        print("  ok  test_signed_message_is_acknowledged_then_processed")

        # * A delivery receipt carries no messages and must not wake the worker.
        receipt = json.dumps({"entry": [{"changes": [{"value": {
            "statuses": [{"id": "wamid.out.1", "status": "read"}]}}]}]}).encode()
        status, _ = _request(base + "/", receipt, _sign(receipt))
        assert status == 200 and bot._work.qsize() == 0, "a status receipt was queued"
        print("  ok  test_status_receipts_are_ignored")

        # ! Meta redelivers on any doubt. The second copy must change nothing.
        before = len(sent)
        status, _ = _request(base + "/", payload, _sign(payload))
        assert status == 200
        bot.work_once(block=False)
        assert len(sent) == before, "a redelivered webhook was answered twice"
        print("  ok  test_redelivery_changes_nothing")
    finally:
        server.shutdown()
        server.server_close()
        whatsapp._post = real_post

    print("test_whatsapp_webhook.py OK")


if __name__ == "__main__":
    run()
