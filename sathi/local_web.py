"""Browser channel for the existing Scheme Sathi conversation.

Run: python -m sathi.local_web                       # local, no event log
     python -m sathi.local_web --db /var/lib/sathi/sathi.db --secure-cookie
                                                     # behind Caddy, see deploy/

# ! Binds to loopback only. In production Caddy owns TLS and proxies to it,
# ! exactly like the WhatsApp webhook. Without --db it writes nothing, which
# ! is the mode for trying the flow on a laptop.
# ! It drives Conversation directly rather than through channels.router, so
# ! slash commands, the reach count and /start sources do not exist here.
# ! Web users appear in the event log as channel "web" and nowhere else.
"""

import argparse
import html
import json
import secrets
import threading
import urllib.request
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from sathi.channels.base import Reply
from sathi.conversation.flow import Conversation, State
from sathi.core.schemes import Scheme, load_all
from sathi.metrics.events import EventLog


_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Yojana Sathi</title><link rel="icon" href="/logo.jpg"><style>
/* Tokens from DESIGN.md (Figma design analysis): monochrome frame, one pastel block, pill buttons. */
:root{--ink:#000;--canvas:#fff;--hairline:#e6e6e6;--soft:#f7f7f5;--block:#dceeb1;--block-2:#c5b0f4;--muted:#5c5c5c}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:var(--canvas);color:var(--ink);font:400 17px/1.5 "Figma Sans",Inter,ui-sans-serif,system-ui,"Noto Sans Devanagari",sans-serif;-webkit-font-smoothing:antialiased}
main{width:min(100%,46rem);margin:auto;padding:clamp(1.5rem,5vw,4rem) 1.1rem 4rem}
.mast{display:grid;grid-template-columns:3.5rem 1fr;column-gap:1rem;align-items:center;padding:0 0 1.5rem;border-bottom:1px solid var(--ink)}
.mast img{width:3.5rem;height:3.5rem;border-radius:9999px;grid-row:1/3}
h1{margin:0;font-weight:700;font-size:clamp(1.6rem,5vw,2.4rem);line-height:1.05;letter-spacing:-.03em}
.note{margin:.35rem 0 0;color:var(--muted);font-size:.95rem}
.card{position:relative;margin-top:2rem;padding:clamp(1.25rem,4vw,2rem);background:var(--block);border-radius:24px;min-height:14rem}
.message{margin:0 0 1.5rem;max-width:36rem;white-space:pre-wrap;font-size:clamp(1.05rem,2vw,1.2rem);font-weight:500;line-height:1.45}
.choices{display:flex;flex-wrap:wrap;gap:.5rem}
.choice,.send,.restart{appearance:none;cursor:pointer;font:600 1rem/1.2 inherit;font-family:inherit;transition:background .12s,color .12s}
.choice{border:1px solid var(--ink);border-radius:50px;background:var(--canvas);color:var(--ink);padding:10px 20px;text-align:left}
.choice:hover{background:var(--ink);color:var(--canvas)}
.choice.scale{width:2.75rem;height:2.75rem;padding:0;text-align:center;border-radius:9999px;flex:0 0 auto}
.choice:focus-visible,.send:focus-visible,.restart:focus-visible,.composer input:focus-visible{outline:2px solid var(--ink);outline-offset:3px}
.composer{display:flex;gap:.5rem;margin-top:1.5rem}
.composer input{min-width:0;flex:1;border:1px solid var(--ink);border-radius:50px;background:var(--canvas);color:var(--ink);font:inherit;padding:10px 18px}
.send{border:1px solid var(--ink);border-radius:50px;background:var(--ink);color:var(--canvas);padding:10px 20px}
.send:hover{background:var(--canvas);color:var(--ink)}
.restart{display:block;margin:1.5rem auto 0;border:0;background:transparent;color:var(--muted);font-size:.9rem;text-decoration:underline;text-underline-offset:3px}
.restart:hover{color:var(--ink)}
.download{display:inline-block;margin-top:1rem;padding:10px 20px;border-radius:50px;background:var(--ink);color:var(--canvas);font-weight:600;text-decoration:none}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
@media(max-width:34rem){.choices{flex-direction:column}.choice{text-align:center}.choices:has(.scale){flex-direction:row;flex-wrap:wrap}.composer{flex-direction:column}.send{text-align:center}}
</style></head><body><main><header class="mast"><img src="/logo.jpg" alt="" width="640" height="640"><h1>योजना साथी<br>Yojana Sathi</h1><p class="note">Answer a few simple questions. Get a clear next step.</p></header><section id="screen" class="card" aria-live="polite"></section><button class="restart" type="button" onclick="restart()">Start again / फिर से शुरू करें</button></main><script>
const screen=document.querySelector('#screen');
function text(value){return String(value||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
function show(data){let out=data.replies.map(r=>`<p class="message">${text(r.text)}</p>${r.buttons?.length?`<div class="choices">${r.buttons.map(b=>`<button class="choice${b.scale?' scale':''}" data-value="${encodeURIComponent(b.value)}">${text(b.label)}</button>`).join('')}</div>`:''}${r.document?`<a class="download" href="${r.document}" download>Download application pack</a>`:''}`).join('');const last=data.replies[data.replies.length-1];const typed=!!(last&&last.typed);if(typed)out+=`<form class="composer"><input name="answer" aria-label="Type an answer" autocomplete="off" placeholder="Type an answer"><button class="send">Send</button></form>`;screen.innerHTML=out;screen.querySelectorAll('.choice').forEach(b=>b.onclick=()=>answer(decodeURIComponent(b.dataset.value)));const form=screen.querySelector('form');if(form){form.onsubmit=e=>{e.preventDefault();const input=e.currentTarget.answer;if(input.value.trim()){answer(input.value);input.value='';}};form.answer.focus();}}
async function answer(value){const r=await fetch('/answer',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({answer:value})});show(await r.json());}
function restart(){answer('/start')}answer('/start');
</script></body></html>"""


# * Read once at import. One file, no static directory, no path handling.
_LOGO = (Path(__file__).resolve().parent / "web" / "logo.jpg").read_bytes()


class LocalWeb:
    """Bounded in-memory browser sessions for local or loopback production use."""

    MAX_SESSIONS = 500
    MAX_DOCUMENTS = 100
    # ! Screens where typing is the ONLY way to answer. Everywhere else the
    # ! buttons are the whole answer and the text box would just be noise.
    # ! Age has no buttons; the free-text occupation screen exists because
    # ! the worker tapped "other"; the suggestion is prose or Skip. State and
    # ! rating take typed input on Telegram, but here they have buttons for
    # ! every value, so they get none.
    TYPED_STATES = frozenset({State.AGE, State.OCCUPATION_FREE, State.SUGGESTION})

    def __init__(self, schemes: dict[str, Scheme], log: EventLog | None = None) -> None:
        self.schemes = schemes
        self.log = log
        self.sessions: dict[str, Conversation] = {}
        self.documents: dict[str, tuple[str, bytes]] = {}
        # ! ThreadingHTTPServer answers each request on its own thread. A
        # ! double-tap on a button is two requests inside one Conversation at
        # ! once; the flow was never written for that. One lock, whole turn.
        # ponytail: global lock; per-session locks if web traffic ever queues.
        self._lock = threading.Lock()

    def turn(self, session: str, answer: str) -> list[Reply]:
        with self._lock:
            return self._turn(session, answer)

    def _turn(self, session: str, answer: str) -> list[Reply]:
        if answer == "/start" or session not in self.sessions:
            # ! Browser cookies are random routing keys, never event identifiers.
            # ponytail: FIFO cap; use expiry only if real traffic reaches this limit.
            while len(self.sessions) >= self.MAX_SESSIONS:
                self.sessions.pop(next(iter(self.sessions)))
            convo = Conversation(self.schemes, self.log, channel="web")
            # ponytail: the cookie is per browser session, so a web "person"
            # ponytail: is one tab until restart; add a long-lived uid cookie
            # ponytail: if cross-visit dedupe ever matters.
            if self.log is not None:
                convo.person = self.log.anon_id(session)
            self.sessions[session] = convo
            return convo.start()
        return self.sessions[session].handle(answer)

    def payload(self, session: str, answer: str) -> bytes:
        replies = self.turn(session, answer)
        convo = self.sessions.get(session)
        typed = convo is not None and convo.state in self.TYPED_STATES
        body = []
        for reply in replies:
            buttons = [{"label": b.label, "value": b.value} for b in reply.buttons]
            # * A browser has room for a 1–10 row; a WhatsApp list does not (ten
            # * rows is its ceiling, and Skip makes eleven). So the scale is
            # * added here, on this channel only. The value is the same digit
            # * string the flow already accepts typed, so nothing else changes.
            if convo is not None and convo.state is State.RATING and reply is replies[-1]:
                buttons = [{"label": str(n), "value": str(n), "scale": True}
                           for n in range(1, 11)] + buttons
            item = {"text": reply.text, "buttons": buttons, "typed": typed}
            if reply.document:
                with self._lock:
                    while len(self.documents) >= self.MAX_DOCUMENTS:
                        self.documents.pop(next(iter(self.documents)))
                    token = secrets.token_urlsafe(20)
                    self.documents[token] = reply.document
                item["document"] = f"/document/{token}"
            body.append(item)
        return json.dumps({"replies": body}, ensure_ascii=False).encode("utf-8")


def handler_class(app: LocalWeb, secure_cookie: bool = False) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _session(self) -> str:
            cookie = self.headers.get("Cookie", "")
            for part in cookie.split(";"):
                key, _, value = part.strip().partition("=")
                # ! Only an id this server issued is a session. A client that
                # ! sends its own value gets a fresh one, so nobody can pick a
                # ! guessable key and share a Conversation with a stranger.
                if key == "sathi_local" and value in app.sessions:
                    return value
            return secrets.token_urlsafe(20)

        def _send(self, status: int, body: bytes, content_type: str, session: str = "") -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            if session:
                flag = "; Secure" if secure_cookie else ""
                self.send_header("Set-Cookie", f"sathi_local={session}; HttpOnly; SameSite=Strict{flag}")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/":
                self._send(HTTPStatus.OK, _PAGE.encode("utf-8"), "text/html; charset=utf-8")
                return
            if self.path == "/logo.jpg":
                self._send(HTTPStatus.OK, _LOGO, "image/jpeg")
                return
            token = self.path.removeprefix("/document/")
            document = app.documents.get(token) if self.path.startswith("/document/") else None
            if document:
                name, blob = document
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Disposition", f"attachment; filename={html.escape(name, quote=True)}")
                self.send_header("Content-Length", str(len(blob)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(blob)
                return
            self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain; charset=utf-8")

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/answer":
                self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain; charset=utf-8")
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                data = json.loads(self.rfile.read(min(size, 10_000)))
                answer = data.get("answer", "")
                if not isinstance(answer, str):
                    raise ValueError
            except (ValueError, json.JSONDecodeError):
                self._send(HTTPStatus.BAD_REQUEST, b"bad request", "text/plain; charset=utf-8")
                return
            session = self._session()
            self._send(HTTPStatus.OK, app.payload(session, answer), "application/json; charset=utf-8", session)

        def log_message(self, *args) -> None:
            pass  # ! Browser input can be sensitive; never write it to stdout.

    return Handler


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run the local Scheme Sathi web experiment")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--db", default="", help="event database; omit for local-only use")
    ap.add_argument("--secure-cookie", action="store_true", help="require HTTPS cookies")
    args = ap.parse_args(argv)
    log = EventLog(args.db) if args.db else None
    app = LocalWeb(load_all(Path("data/schemes")), log)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_class(app, args.secure_cookie))
    print(f"Local experiment: http://127.0.0.1:{server.server_address[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        if log:
            log.close()
    return 0


def _self_check() -> None:
    app = LocalWeb(load_all(Path(__file__).resolve().parents[1] / "data/schemes"))
    session = "test"
    start = json.loads(app.payload(session, "/start"))
    assert len(start["replies"][0]["buttons"]) == 2
    hi = json.loads(app.payload(session, "lang:hi"))
    assert hi["replies"][0]["buttons"], hi
    assert hi["replies"][0]["typed"] is False, "consent is buttons only"
    app.sessions[session].state = State.RATING
    rating = json.loads(app.payload(session, "noop"))["replies"][-1]
    assert rating["typed"] is False, "ten buttons and Skip: no text box"
    assert [b["label"] for b in rating["buttons"]][:10] == [str(n) for n in range(1, 11)]
    assert rating["buttons"][-1]["value"] == "skip", rating["buttons"][-1]
    # * The button value goes through the same handler as a typed number.
    app.payload(session, "7")
    assert app.sessions[session]._rating == 7
    assert app.sessions[session].log is None, "no --db means no metrics"
    # ! A cookie the server never issued must not become a session.
    handler = handler_class(app)
    class _Req:  # the two attributes _session() reads
        headers = {"Cookie": "sathi_local=made-up"}
    minted = handler._session(_Req())
    assert minted != "made-up" and minted not in app.sessions
    class _Known:
        headers = {"Cookie": f"sathi_local={session}"}
    assert handler._session(_Known()) == session

    # * One real HTTP turn catches a broken JSON boundary without opening a browser.
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class(app))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/answer"
        request = urllib.request.Request(
            url, data=b'{"answer":"/start"}',
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            page = json.loads(response.read())
            assert response.headers["Cache-Control"] == "no-store"
            assert page["replies"][0]["buttons"], page
    finally:
        server.shutdown()
        server.server_close()
    print("local_web.py OK")


if __name__ == "__main__":
    raise SystemExit(main())
