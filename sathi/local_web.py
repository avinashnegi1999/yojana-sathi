"""Browser channel for the existing Scheme Sathi conversation.

Run: python -m sathi.local_web                       # local, no event log
     python -m sathi.local_web --db /var/lib/sathi/sathi.db --secure-cookie
                                                     # behind Caddy, see deploy/

# ! Binds to loopback only. In production Caddy owns TLS and proxies to it,
# ! exactly like the WhatsApp webhook. Without --db it writes nothing, which
# ! is the mode for trying the flow on a laptop.
# ! It drives Conversation directly rather than through channels.router, so
# ! slash commands and the reach count do not exist here. An arrival slug does:
# ! /?start=csc tags the session's events with cohort "csc", exactly as
# ! t.me/YojanaSathiBot?start=csc does on Telegram.
# ! Web users appear in the event log as channel "web" and nowhere else.
#
# ! This is a public endpoint behind Caddy, so it carries the same guards as
# ! the WhatsApp webhook (AUDIT.md M6): one exact, bounded Content-Length, a
# ! socket timeout, a JSON object or a 400, a turn that fails becomes a
# ! message instead of a dropped connection, idle sessions expire, and one
# ! client cannot mint enough sessions to push everyone else out.
"""

import argparse
import html
import json
import secrets
import threading
import time
import urllib.request
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from sathi.channels.base import Reply
from sathi.conversation.flow import Conversation, State
from sathi.core.content import DEFAULT_LANG, LANGS, s
from sathi.core.schemes import Scheme, load_all
from sathi.metrics.events import SOURCE_SLUGS, EventLog


_PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#f5f5f7">
<title>Yojana Sathi · योजना साथी</title><link rel="icon" href="/logo.jpg"><style>
/* Apple-inspired: parchment canvas, near-black ink, ONE blue for actions, system
   fonts only (SF on Apple devices), no shadows, no gradients, pills and 18px cards.
   Reference: getdesign "apple" DESIGN.md — design language only, no Apple assets. */
:root{--ink:#1d1d1f;--body:#333333;--muted:#6e6e73;--blue:#0066cc;--focus:#0071e3;--canvas:#ffffff;--parchment:#f5f5f7;--hairline:#e0e0e0}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;min-height:100vh;background:var(--parchment);color:var(--ink);font:400 17px/1.47 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans Devanagari","Nirmala UI",sans-serif;-webkit-font-smoothing:antialiased}
html:lang(en) body{letter-spacing:-.022em}
html:lang(hi) body{line-height:1.6}
.bar{position:sticky;top:0;z-index:2;background:rgba(245,245,247,.8);-webkit-backdrop-filter:saturate(180%) blur(20px);backdrop-filter:saturate(180%) blur(20px);border-bottom:1px solid rgba(0,0,0,.08)}
.bar-in{max-width:40rem;margin:0 auto;min-height:52px;display:flex;align-items:center;gap:10px;padding:0 16px}
.bar img{width:28px;height:28px;border-radius:50%;flex:0 0 auto}
.brand{font-weight:600;font-size:17px;letter-spacing:0;white-space:nowrap}
.switch{margin-left:auto;appearance:none;border:1px solid var(--hairline);background:var(--canvas);color:var(--ink);font:inherit;font-size:14px;cursor:pointer;min-height:32px;padding:0 14px;border-radius:16px;white-space:nowrap}
.switch:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.restart{appearance:none;border:0;background:none;color:var(--blue);font:inherit;font-size:14px;cursor:pointer;min-height:44px;padding:0 2px;white-space:nowrap}
main{max-width:40rem;margin:0 auto;padding:40px 16px 96px}
.q{margin:8px 0 24px;font-size:28px;font-weight:600;line-height:1.18;letter-spacing:-.01em;white-space:pre-wrap}
html:lang(hi) .q{line-height:1.4;letter-spacing:0}
.q:has(+ .lead){margin-bottom:10px}
.q2{margin:32px 0 16px;font-size:22px;font-weight:600;line-height:1.3}
.recap{margin:0 0 24px;border-bottom:1px solid var(--hairline);padding-bottom:12px}
.recap summary{cursor:pointer;color:var(--blue);font-size:15px;min-height:44px;display:flex;align-items:center;list-style:none}
.recap summary::-webkit-details-marker{display:none}
.recap summary::after{content:"›";margin-left:6px;transition:transform .15s}
.recap[open] summary::after{transform:rotate(90deg)}
.recap .message{margin:4px 0 0;font-size:15px;color:var(--muted)}
.lead{margin:0 0 24px;white-space:pre-wrap;color:var(--muted);font-size:19px;line-height:1.5}
@media(min-width:736px){main{padding-top:64px}.q{font-size:34px}}

.message{margin:0 0 16px;white-space:pre-wrap;color:var(--body)}
.scheme{background:var(--canvas);border:1px solid var(--hairline);border-radius:18px;padding:20px 22px;margin:0 0 12px}
.scheme-name{margin:0 0 6px;font-weight:600;color:var(--ink);line-height:1.35}
.scheme-body{margin:0;white-space:pre-wrap;color:var(--body)}
.choices{display:flex;flex-direction:column;gap:10px;margin:0 0 8px}
.choice{appearance:none;display:flex;align-items:center;justify-content:space-between;gap:12px;width:100%;min-height:52px;padding:13px 22px;text-align:left;background:var(--canvas);color:var(--ink);border:1px solid var(--hairline);border-radius:26px;font:inherit;cursor:pointer;transition:transform .12s ease}
.choice:active{transform:scale(.98)}
.choice.primary{justify-content:center;background:var(--blue);border-color:var(--blue);color:#fff;font-weight:600}
.choice.selected{border:2px solid var(--focus);padding:12px 21px}
.choice .tick{color:var(--focus);font-weight:600}
.choices:has(.scale){display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.choices:has(.scale) .choice:not(.scale){grid-column:1/-1;justify-content:center}
.choice.scale{justify-content:center;min-height:52px;padding:0;border-radius:26px}
.composer{display:flex;gap:10px;margin:0 0 8px}
.composer input{flex:1;min-width:0;height:52px;border:1px solid var(--hairline);border-radius:26px;background:var(--canvas);color:var(--ink);font:inherit;padding:0 20px}
.send{appearance:none;border:0;border-radius:26px;background:var(--blue);color:#fff;font:inherit;font-weight:600;padding:0 26px;height:52px;cursor:pointer}
.send:active{transform:scale(.98)}
.download{display:inline-flex;align-items:center;min-height:52px;margin:0 0 24px;padding:0 26px;border-radius:26px;background:var(--blue);color:#fff;font-weight:600;text-decoration:none}
.choice:focus-visible,.send:focus-visible,.restart:focus-visible,.download:focus-visible,.composer input:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style></head><body>
<header class="bar"><div class="bar-in"><img src="/logo.jpg" alt="" width="28" height="28"><span class="brand" id="brand">Yojana Sathi</span><button class="switch" id="switch" type="button" onclick="switchLang()" lang="hi">हिंदी</button><button class="restart" id="restart" type="button" onclick="restart()">Start again</button></div></header>
<main><section id="screen" aria-live="polite"></section></main>
<script>
const screen=document.querySelector('#screen');
const UI={hi:{type:'यहाँ लिखें',send:'भेजें',download:'अपना काग़ज़ डाउनलोड करें',restart:'फिर से शुरू',other:'English',otherLang:'en',brand:'योजना साथी',answers:'आपके जवाब'},en:{type:'Type your answer',send:'Send',download:'Download your sheet',restart:'Start again',other:'हिंदी',otherLang:'hi',brand:'Yojana Sathi',answers:'Your answers'}};
let current='en';
// The one blue pill on a screen: the forward action, never an answer to a yes/no question.
const PRIMARY=new Set(['consent_yes','pick:all','pick:done','next']);
function text(value){return String(value||'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function blocks(value,headline,cls){cls=cls||'q';return String(value||'').split(/\n\s*\n/).map((b,i)=>{if(headline&&i===0){const cut=b.indexOf('\n');return cut<0?`<h2 class="${cls}">${text(b)}</h2>`:`<h2 class="${cls}">${text(b.slice(0,cut))}</h2><p class="lead">${text(b.slice(cut+1))}</p>`;}const m=b.match(/^(\d+\.\s[^\n]*)\n([\s\S]*)$/);return m?`<div class="scheme"><p class="scheme-name">${text(m[1])}</p><p class="scheme-body">${text(m[2].replace(/^ +/gm,''))}</p></div>`:`<p class="message">${text(b)}</p>`;}).join('');}
function button(b){const picked=b.label.startsWith('✅ ');const label=picked?b.label.slice(2):b.label;const cls=['choice',b.scale?'scale':'',PRIMARY.has(b.value)?'primary':'',picked?'selected':''].filter(Boolean).join(' ');return `<button class="${cls}" data-value="${encodeURIComponent(b.value)}"${picked?' aria-pressed="true"':''}><span>${text(label)}</span>${picked?'<span class="tick" aria-hidden="true">✓</span>':''}</button>`;}
function show(data){const ui=UI[data.lang]||UI.hi;document.documentElement.lang=data.lang==='en'?'en':'hi';document.getElementById('restart').textContent=ui.restart;current=data.lang==='hi'?'hi':'en';const sw=document.getElementById('switch');sw.textContent=ui.other;sw.lang=ui.otherLang;document.getElementById('brand').textContent=ui.brand;const last=data.replies.length-1;const hasResult=data.replies.some(r=>r.kind==='result');let out=data.replies.map((r,i)=>{if(r.kind==='recap'){const body=r.text.split('\n').slice(1).join('\n');return `<details class="recap"><summary>${ui.answers}</summary><p class="message">${text(body)}</p></details>`;}const asks=i===last&&(r.buttons?.length||r.typed);return `${r.kind==='result'?blocks(r.text,true,'q'):blocks(r.text,asks,hasResult?'q2':'q')}${r.buttons?.length?`<div class="choices">${r.buttons.map(button).join('')}</div>`:''}${r.document?`<a class="download" href="${r.document}" download>${ui.download}</a>`:''}`;}).join('');const typed=!!(data.replies[last]&&data.replies[last].typed);if(typed)out+=`<form class="composer"><input name="answer" aria-label="${ui.type}" autocomplete="off" inputmode="text" placeholder="${ui.type}"><button class="send">${ui.send}</button></form>`;screen.innerHTML=out;window.scrollTo({top:0});screen.querySelectorAll('.choice').forEach(b=>b.onclick=()=>answer(decodeURIComponent(b.dataset.value)));const form=screen.querySelector('form');if(form){form.onsubmit=e=>{e.preventDefault();const input=e.currentTarget.answer;if(input.value.trim()){answer(input.value);input.value='';}};form.answer.focus();}}
const START=(()=>{const src=new URLSearchParams(location.search).get('start')||'';return /^[a-z]{1,20}$/.test(src)?'/start '+src:'/start';})();
function oops(){screen.innerHTML=`<h2 class="q">${text('कुछ गड़बड़ हो गई।\nSomething went wrong.')}</h2><div class="choices"><button class="choice primary" onclick="restart()">फिर से शुरू · Start again</button></div>`;}
async function answer(value){try{const r=await fetch('/answer',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({answer:value})});const data=await r.json().catch(()=>null);if(data&&Array.isArray(data.replies)){show(data);}else{oops();}}catch(e){oops();}}
function switchLang(){answer('/lang '+(current==='en'?'hi':'en'))}
function restart(){answer(START)}answer(START);
</script></body></html>"""


# * Read once at import. One file, no static directory, no path handling.
_LOGO = (Path(__file__).resolve().parent / "web" / "logo.jpg").read_bytes()


class LocalWeb:
    """Bounded in-memory browser sessions for local or loopback production use."""

    # ! A session nobody has touched for 30 minutes is dropped, answers and
    # ! all. The README promises the profile is discarded; a worker who walks
    # ! away mid-screening used to leave her age, widow status and disability
    # ! answer in RAM until the next restart (AUDIT.md M8).
    SESSION_IDLE_SECONDS = 30 * 60
    MAX_SESSIONS = 500
    # ! A sheet carries the answer recap. Same one-hour life as a Telegram pack
    # ! link (sathi/pack/links.py), not "until 100 more have been made".
    DOCUMENT_SECONDS = 60 * 60
    MAX_DOCUMENTS = 100
    # ! One client may open this many new sessions per window. Before this,
    # ! 500 anonymous POSTs evicted every live worker (AUDIT.md M6). A CSC
    # ! operator helping a queue of workers from one office stays far below it.
    NEW_SESSIONS_PER_CLIENT = 30
    NEW_SESSION_WINDOW_SECONDS = 10 * 60
    # ! Screens where typing is the ONLY way to answer. Everywhere else the
    # ! buttons are the whole answer and the text box would just be noise.
    # ! Age has no buttons; the free-text occupation screen exists because
    # ! the worker tapped "other"; the suggestion is prose or Skip. State and
    # ! rating take typed input on Telegram, but here they have buttons for
    # ! every value, so they get none.
    TYPED_STATES = frozenset({State.AGE, State.OCCUPATION_FREE, State.SUGGESTION})
    # * The language a new browser session opens in; see _turn().
    DEFAULT_LANG = "en"

    def __init__(self, schemes: dict[str, Scheme], log: EventLog | None = None,
                 clock=time.monotonic) -> None:
        self.schemes = schemes
        self.log = log
        self.clock = clock  # * injectable so the self-check can age sessions
        self.sessions: dict[str, Conversation] = {}
        self._last_seen: dict[str, float] = {}
        # * token -> (filename, bytes, created at)
        self.documents: dict[str, tuple[str, bytes, float]] = {}
        self._new_by_client: dict[str, deque[float]] = {}
        # ! ThreadingHTTPServer answers each request on its own thread. A
        # ! double-tap on a button is two requests inside one Conversation at
        # ! once; the flow was never written for that. One lock, whole turn.
        # ponytail: global lock; per-session locks if web traffic ever queues.
        self._lock = threading.Lock()

    # * ---------------------------------------------------------- housekeeping

    def _sweep(self, now: float) -> None:
        """Drop idle sessions and expired sheets. Caller holds the lock."""
        for key in [k for k, seen in self._last_seen.items()
                    if now - seen > self.SESSION_IDLE_SECONDS]:
            self.sessions.pop(key, None)
            self._last_seen.pop(key, None)
        for token in [t for t, (_, _, made) in self.documents.items()
                      if now - made > self.DOCUMENT_SECONDS]:
            del self.documents[token]
        for client in list(self._new_by_client):
            recent = self._new_by_client[client]
            while recent and now - recent[0] > self.NEW_SESSION_WINDOW_SECONDS:
                recent.popleft()
            if not recent:
                del self._new_by_client[client]

    def _may_open_session(self, client: str, now: float) -> bool:
        """Count one new session for this client, or refuse. Caller holds the lock."""
        recent = self._new_by_client.setdefault(client, deque())
        if len(recent) >= self.NEW_SESSIONS_PER_CLIENT:
            return False
        recent.append(now)
        return True

    # * ------------------------------------------------------------------ turns

    def turn(self, session: str, answer: str, client: str = "local") -> list[Reply] | None:
        """One answer in, replies out. None means this client is over its limit."""
        with self._lock:
            now = self.clock()
            self._sweep(now)
            return self._turn(session, answer, client, now)

    def _turn(self, session: str, answer: str, client: str, now: float) -> list[Reply] | None:
        words = answer.strip().split()
        if words[:1] == ["/start"] or session not in self.sessions:
            if not self._may_open_session(client, now):
                return None
            # ! When full even after the idle sweep, drop the session idle the
            # ! longest — never the one somebody tapped a second ago.
            while len(self.sessions) >= self.MAX_SESSIONS:
                oldest = min(self._last_seen, key=self._last_seen.get)
                self.sessions.pop(oldest, None)
                self._last_seen.pop(oldest, None)
            # * "/start csc" from the page's ?start=csc. Unknown slugs are
            # * ignored, never stored.
            slug = words[1].lower() if len(words) > 1 and words[0] == "/start" else ""
            convo = Conversation(self.schemes, self.log, channel="web",
                                 cohort=slug if slug in SOURCE_SLUGS else None)
            # ! Browser cookies are random routing keys, never event identifiers.
            # ponytail: the cookie is per browser session, so a web "person"
            # ponytail: is one tab until restart; add a long-lived uid cookie
            # ponytail: if cross-visit dedupe ever matters.
            if self.log is not None:
                convo.person = self.log.feedback_id(session)
            self.sessions[session] = convo
            self._last_seen[session] = now
            # * The browser opens in English, straight at the consent screen:
            # * most web visitors read English, and the language question was
            # * one more tap before anything happened. Hindi is one tap away
            # * in the top bar ("/lang hi" below). Telegram and WhatsApp keep
            # * their bilingual language question as the first screen.
            convo.start()
            return convo.handle(f"lang:{self.DEFAULT_LANG}")
        self._last_seen[session] = now
        convo = self.sessions[session]
        if words[:1] == ["/lang"] and len(words) == 2 and words[1] in ("hi", "en"):
            # * The top-bar switch. Keeps every answer and re-asks the current
            # * question in the other language.
            return [convo.set_language(words[1])[-1]]
        return convo.handle(answer)

    def payload(self, session: str, answer: str, client: str = "local") -> tuple[int, bytes]:
        """(HTTP status, JSON body). A failed turn is a message, never a dropped socket."""
        try:
            replies = self.turn(session, answer, client)
        except Exception as e:  # noqa: BLE001 — one broken session must not take the page down
            # ! Same rule as the Telegram adapter: the turn may have half-applied,
            # ! so the answers go and the worker is told to start again. Type
            # ! name only in the log — the message could echo what she typed.
            print(f"[web] turn failed: {type(e).__name__}")
            with self._lock:
                convo = self.sessions.pop(session, None)
                self._last_seen.pop(session, None)
            lang = convo.lang if convo is not None else DEFAULT_LANG
            return 500, self._message(s("errors.web_stopped", lang))
        if replies is None:
            # * Before a language is chosen, so both languages.
            text = "\n\n".join(s("errors.too_many_sessions", lang) for lang in LANGS)
            return 429, self._message(text)

        convo = self.sessions.get(session)
        typed = convo is not None and convo.state in self.TYPED_STATES
        body = []
        # * Which reply is the answer recap and which is the result, so the page
        # * can lead with the result and fold the recap away. Matched on the
        # * recap's own header string, never guessed from layout.
        recap_header = s("recap.header", convo.lang) if convo is not None else None
        after_recap = False
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
            if recap_header and reply.text.startswith(recap_header):
                item["kind"] = "recap"
                after_recap = True
            elif after_recap:
                item["kind"] = "result"
                after_recap = False
            if reply.document:
                with self._lock:
                    while len(self.documents) >= self.MAX_DOCUMENTS:
                        oldest = min(self.documents, key=lambda t: self.documents[t][2])
                        del self.documents[oldest]
                    token = secrets.token_urlsafe(20)
                    name, blob = reply.document
                    self.documents[token] = (name, blob, self.clock())
                item["document"] = f"/document/{token}"
            body.append(item)
        # * The page labels its own controls (Send, the text box, Download) in
        # * the worker's language; they were English on a Hindi screen.
        lang = convo.lang if convo is not None else DEFAULT_LANG
        return 200, json.dumps({"replies": body, "lang": lang}, ensure_ascii=False).encode("utf-8")

    def document(self, token: str) -> tuple[str, bytes] | None:
        """A sheet by its token, or None once it has expired."""
        with self._lock:
            self._sweep(self.clock())
            entry = self.documents.get(token)
        return (entry[0], entry[1]) if entry else None

    @staticmethod
    def _message(text: str) -> bytes:
        return json.dumps({"replies": [{"text": text, "buttons": [], "typed": False}]},
                          ensure_ascii=False).encode("utf-8")


# ! The largest body a real turn sends is a button value or a short typed
# ! answer. Ten thousand bytes is generous; anything bigger is refused unread.
MAX_BODY = 10_000


def handler_class(app: LocalWeb, secure_cookie: bool = False) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def setup(self) -> None:
            # ! A client that opens a socket and sends nothing must not hold a
            # ! server thread forever. Same guard as the pack and WhatsApp servers.
            self.request.settimeout(10)
            super().setup()

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

        def _client(self) -> str:
            """Who is asking, for the new-session limit only. Never logged or stored.

            # * This server binds loopback, so in production every peer is
            # * Caddy. Caddy appends the real client to X-Forwarded-For, so the
            # * LAST entry is the one Caddy wrote; earlier entries are whatever
            # * the client claimed and are ignored.
            """
            forwarded = self.headers.get("X-Forwarded-For", "")
            if forwarded:
                return forwarded.split(",")[-1].strip()
            return self.client_address[0]

        def _send(self, status: int, body: bytes, content_type: str, session: str = "") -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            if session:
                flag = "; Secure" if secure_cookie else ""
                self.send_header("Set-Cookie", f"sathi_local={session}; HttpOnly; SameSite=Strict{flag}")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                # * The client hung up before reading the reply. Nothing to do,
                # * and not worth a traceback in the journal.
                self.close_connection = True

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/" or self.path.startswith("/?"):
                self._send(HTTPStatus.OK, _PAGE.encode("utf-8"), "text/html; charset=utf-8")
                return
            if self.path == "/logo.jpg":
                self._send(HTTPStatus.OK, _LOGO, "image/jpeg")
                return
            token = self.path.removeprefix("/document/")
            document = app.document(token) if self.path.startswith("/document/") else None
            if document:
                name, blob = document
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Disposition", f"attachment; filename={html.escape(name, quote=True)}")
                self.send_header("Content-Length", str(len(blob)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("Referrer-Policy", "no-referrer")
                self.end_headers()
                self.wfile.write(blob)
                return
            self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain; charset=utf-8")

        def _bad(self, status: int = HTTPStatus.BAD_REQUEST) -> None:
            self.close_connection = True
            self._send(status, b"bad request", "text/plain; charset=utf-8")

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/answer":
                self._send(HTTPStatus.NOT_FOUND, b"not found", "text/plain; charset=utf-8")
                return
            # ! One Content-Length, a real non-negative number, no chunked
            # ! body. A negative length used to reach rfile.read(-1), which
            # ! reads until the client hangs up.
            lengths = self.headers.get_all("Content-Length") or []
            if len(lengths) != 1 or self.headers.get("Transfer-Encoding"):
                self._bad()
                return
            try:
                size = int(lengths[0])
            except ValueError:
                self._bad()
                return
            if size < 0:
                self._bad()
                return
            if size > MAX_BODY:
                self._bad(HTTPStatus.REQUEST_ENTITY_TOO_LARGE)
                return
            try:
                raw = self.rfile.read(size)
            except TimeoutError:
                self._bad(HTTPStatus.REQUEST_TIMEOUT)
                return
            if len(raw) != size:
                self._bad()
                return
            try:
                data = json.loads(raw)
            except (ValueError, RecursionError):
                self._bad()
                return
            # ! A JSON array or number used to reach data.get() and crash the
            # ! handler with AttributeError. Only an object with a string answer.
            answer = data.get("answer") if isinstance(data, dict) else None
            if not isinstance(answer, str):
                self._bad()
                return
            session = self._session()
            status, body = app.payload(session, answer, self._client())
            self._send(status, body, "application/json; charset=utf-8",
                       session if status == 200 else "")

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
    import http.client
    import socket
    import tempfile

    schemes = load_all(Path(__file__).resolve().parents[1] / "data/schemes")

    def body(result: tuple[int, bytes]) -> dict:
        status, raw = result
        assert status == 200, (status, raw[:200])
        return json.loads(raw)

    app = LocalWeb(schemes)
    session = "test"
    start = body(app.payload(session, "/start"))
    # * The browser opens in English at consent, not at the language question.
    assert start["lang"] == "en" and app.sessions[session].state is State.CONSENT
    assert len(start["replies"][0]["buttons"]) == 2
    assert start["replies"][0]["typed"] is False, "consent is buttons only"
    # * The top-bar switch keeps the session and re-asks the same question.
    hi = body(app.payload(session, "/lang hi"))
    assert hi["lang"] == "hi" and app.sessions[session].state is State.CONSENT
    assert hi["replies"][-1]["buttons"], hi
    app.sessions[session].state = State.RATING
    rating = body(app.payload(session, "noop"))["replies"][-1]
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

    # ! A turn that raises becomes a message and a dropped session, never a
    # ! dropped connection that freezes the page (AUDIT.md M6).
    app.sessions[session].state = State.RATING
    app.sessions[session].handle = lambda answer: 1 / 0
    status, raw = app.payload(session, "7")
    assert status == 500 and session not in app.sessions
    assert s("errors.web_stopped", "hi") in json.loads(raw)["replies"][0]["text"]

    # ! Idle sessions and old sheets expire (AUDIT.md M8). The clock is fake.
    now = [1000.0]
    aged = LocalWeb(schemes, clock=lambda: now[0])
    aged.payload("a", "/start")
    aged.documents["tok"] = ("sheet.html", b"x", now[0])
    now[0] += LocalWeb.SESSION_IDLE_SECONDS - 1
    aged.payload("b", "/start")
    assert "a" in aged.sessions and aged.document("tok") is not None
    now[0] += 2
    aged.payload("b", "lang:hi")
    assert "a" not in aged.sessions, "an idle session must be dropped"
    assert "b" in aged.sessions, "an active one must not"
    now[0] += LocalWeb.DOCUMENT_SECONDS
    assert aged.document("tok") is None, "a sheet must expire after an hour"

    # ! One client cannot mint sessions without limit, and others are unaffected.
    limited = LocalWeb(schemes, clock=lambda: now[0])
    for i in range(LocalWeb.NEW_SESSIONS_PER_CLIENT):
        assert limited.payload(f"s{i}", "/start", client="203.0.113.9")[0] == 200
    status, raw = limited.payload("one-more", "/start", client="203.0.113.9")
    assert status == 429 and "one-more" not in limited.sessions
    assert limited.payload("neighbour", "/start", client="198.51.100.4")[0] == 200
    # * The limit is a window, not a ban.
    now[0] += LocalWeb.NEW_SESSION_WINDOW_SECONDS + 1
    assert limited.payload("later", "/start", client="203.0.113.9")[0] == 200

    # * The page's ?start=csc reaches the event log as the session's cohort.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        log = EventLog(Path(d) / "web.db")
        tagged = LocalWeb(schemes, log)
        tagged.payload("p", "/start csc")
        tagged.payload("p", "lang:en")
        tagged.payload("p", "consent_yes")
        tagged.payload("q", "/start not-a-slug")
        assert tagged.sessions["p"].session.cohort == "csc"
        assert tagged.sessions["q"].session.cohort is None
        log.close()

    # * Real HTTP: the JSON boundary, and every malformed body a 400, not a crash.
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class(app))
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{port}/answer"
        request = urllib.request.Request(
            url, data=b'{"answer":"/start"}',
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            page = json.loads(response.read())
            assert response.headers["Cache-Control"] == "no-store"
            assert page["replies"][0]["buttons"], page

        for bad in (b"[1,2]", b"42", b'{"answer": 7}', b"not json", b"{}"):
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            conn.request("POST", "/answer", body=bad, headers={"Content-Type": "application/json"})
            assert conn.getresponse().status == 400, bad
            conn.close()

        # ! A negative length used to hang the thread reading to end of stream.
        raw_socket = socket.create_connection(("127.0.0.1", port), timeout=5)
        raw_socket.sendall(b"POST /answer HTTP/1.1\r\nHost: x\r\nContent-Length: -1\r\n\r\n{}")
        assert raw_socket.recv(64).startswith(b"HTTP/1.0 400"), "negative length not refused"
        raw_socket.close()

        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("POST", "/answer", body=b"x" * (MAX_BODY + 1),
                      headers={"Content-Type": "application/json"})
        assert conn.getresponse().status == 413
        conn.close()
    finally:
        server.shutdown()
        server.server_close()
    print("local_web.py OK")


if __name__ == "__main__":
    raise SystemExit(main())
