"""Offline WhatsApp boundary regressions; run directly or through check.py.

# * Exercises the production HTTP handler and worker with a fake outbound wire.
# * Does not contact Meta, use credentials, or certify production approval.
"""

import contextlib
import http.client
import io
import json
import queue
import signal
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sathi.channels import whatsapp
from sathi.channels.base import Button, Reply
from test_whatsapp_webhook import SCHEMES, SECRET, VERIFY, _message, _sign


def test_http_boundary() -> None:
    bot = whatsapp.WhatsAppBot(SCHEMES, token="t", phone_number_id="1",
                              app_secret=SECRET, verify_token=VERIFY)
    server = ThreadingHTTPServer(("127.0.0.1", 0), whatsapp._webhook_handler(bot))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(body: bytes, headers: dict | None = None) -> int:
        connection = http.client.HTTPConnection(*server.server_address, timeout=3)
        try:
            connection.request("POST", "/", body, headers or {
                "x-hub-signature-256": _sign(body)})
            response = connection.getresponse()
            response.read()
            return response.status
        finally:
            connection.close()

    try:
        for payload in ([], None, {"entry": [None]}, {"entry": [{"changes": [None]}]},
                        {"entry": [{"changes": [{"value": {"messages": [None]}}]}]}):
            assert request(json.dumps(payload).encode()) == 400, "invalid shape was acknowledged"
        for length in ("-1", "invalid"):
            assert request(b"", {"content-length": length}) == 400
        assert request(b"", {"content-length": str(1024 * 1024)}) == 413
        assert request(b"", {"x-hub-signature-256": "sha256=é"}) == 403
        connection = http.client.HTTPConnection(*server.server_address, timeout=3)
        try:
            connection.request("GET", "/?hub.mode=subscribe&hub.verify_token=%C3%A9")
            response = connection.getresponse()
            assert response.status == 403
            response.read()
        finally:
            connection.close()
        invalid = _message("/start")
        invalid["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = []
        assert request(json.dumps(invalid).encode()) == 400
        other_number = _message("/start")
        other_number["entry"][0]["changes"][0]["value"]["metadata"] = {"phone_number_id": "other"}
        assert request(json.dumps(other_number).encode()) == 200
        assert bot._work.qsize() == 0, "another business number reached this bot"
        bot._work = queue.Queue(maxsize=1)
        payload = json.dumps(_message("/start")).encode()
        assert request(payload) == 200
        assert bot._work.qsize() == 1, "200 preceded queue acceptance"
        assert request(payload) == 503, "a full queue acknowledged lost work"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_batch_failure_isolation_and_private_logs() -> None:
    bot = whatsapp.WhatsAppBot(SCHEMES, token="t", phone_number_id="1",
                              app_secret=SECRET, verify_token=VERIFY)
    original = whatsapp._post
    sent = []
    private_marker = "PRIVATE_PROVIDER_DETAIL"

    def send(token, path, payload):
        if payload["to"] == "911":
            raise whatsapp.WhatsAppError(private_marker, 400)
        sent.append(payload)
        return {"messages": [{"id": "out.1"}]}

    whatsapp._post = send
    try:
        values = [_message("/start", sender, "in." + sender)["entry"][0]["changes"][0]["value"]
                  for sender in ("911", "922")]
        bot.enqueue({"messages": [v["messages"][0] for v in values]})
        capture = io.StringIO()
        with contextlib.redirect_stdout(capture):
            assert bot.work_once(block=False)
        assert "922" in bot.sessions, "one failed recipient discarded another recipient's message"
        assert "911" not in bot.sessions
        assert len(sent) == 1
        assert private_marker not in capture.getvalue(), "provider details leaked into logs"
    finally:
        whatsapp._post = original


def test_complete_text_and_context_required() -> None:
    bot = whatsapp.WhatsAppBot(SCHEMES, token="t", phone_number_id="1",
                              app_secret=SECRET, verify_token=VERIFY)
    original = whatsapp._post
    sent = []
    whatsapp._post = lambda token, path, payload: (
        sent.append(payload) or {"messages": [{"id": f"out.{len(sent)}"}]})
    try:
        text = "स्रोत और आवेदन की पूरी जानकारी। " * 300
        for buttons in ((), (Button("हाँ", "yes"),)):
            sent.clear()
            bot.send("911", Reply(text=text, buttons=buttons))
            pieces = [p["text"]["body"] for p in sent if p["type"] == "text"]
            assert "".join(pieces) == text, "long worker guidance was silently truncated"
            assert all(len(piece) <= 4096 for piece in pieces)
        bot.handle_update({"messages": [{"id": "start", "from": "911", "type": "text",
                                          "text": {"body": "/start"}}]})
        bot.handle_update({"messages": [{"id": "tap", "from": "911", "type": "interactive",
                                          "interactive": {"button_reply": {"id": "lang:en"}}}]})
        assert bot.sessions["911"].state.value == "language", "unbound button changed the flow"
    finally:
        whatsapp._post = original


def test_normal_shutdown_drains_before_returning(shutdown_signal=None) -> None:
    bot = whatsapp.WhatsAppBot(SCHEMES, token="t", phone_number_id="1",
                              app_secret=SECRET, verify_token=VERIFY)
    original_server, original_post = whatsapp.ThreadingHTTPServer, whatsapp._post
    receiver_closed = threading.Event()
    completed = []
    workers = []
    previous_term = signal.getsignal(signal.SIGTERM)

    class StoppedServer(ThreadingHTTPServer):
        def serve_forever(self):
            workers.extend(t for t in threading.enumerate() if t.name == "sathi-whatsapp")
            for sender in ("911", "922"):
                bot.enqueue(_message("/start", sender, "stop." + sender)["entry"][0]["changes"][0]["value"])
            if shutdown_signal is not None:
                signal.raise_signal(shutdown_signal)
            raise KeyboardInterrupt

        def server_close(self):
            super().server_close()
            receiver_closed.set()

    def send(token, path, payload):
        assert receiver_closed.wait(2), "worker ran after the receiver should have closed"
        completed.append(payload["to"])
        return {"messages": [{"id": "out." + payload["to"]}]}

    whatsapp.ThreadingHTTPServer, whatsapp._post = StoppedServer, send
    try:
        try:
            bot.serve_forever(0)
        except KeyboardInterrupt:
            pass
        assert receiver_closed.is_set(), "shutdown left the HTTP socket open"
        assert completed == ["911", "922"], "shutdown returned before accepted work finished"
        assert workers and all(not worker.is_alive() for worker in workers)
        assert bot._work.unfinished_tasks == 0
        assert signal.getsignal(signal.SIGTERM) == previous_term
    finally:
        receiver_closed.set()
        whatsapp.ThreadingHTTPServer, whatsapp._post = original_server, original_post


def test_sigterm_drains_before_returning() -> None:
    test_normal_shutdown_drains_before_returning(signal.SIGTERM)


def run() -> None:
    failures = []
    for test in (test_http_boundary, test_batch_failure_isolation_and_private_logs,
                 test_complete_text_and_context_required,
                 test_normal_shutdown_drains_before_returning,
                 test_sigterm_drains_before_returning):
        try:
            test()
            print(f"  ok  {test.__name__}")
        except Exception as error:
            failures.append((test.__name__, type(error).__name__, str(error)))
    assert not failures, failures
    print("test_whatsapp_safety.py OK")


if __name__ == "__main__":
    run()
