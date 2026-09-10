"""Hand the worker a link to her pack instead of a file.

# ! WHY THIS EXISTS: WhatsApp refuses `text/html`, so `pack_as_text()` flattens
# ! the sheet to plain text and the layout is lost. Telegram accepts the file
# ! but many Android builds open it in a viewer that cannot render it. A link
# ! opens in the phone's own browser, which renders Devanagari properly and
# ! offers "Save as PDF" in its print sheet.
#
# ! THE INVARIANT THIS MUST NOT BREAK. `sathi/pack/pack.py` says the pack "is
# ! never written to disk on the server — there is no packs/ directory in
# ! production and no cleanup job to forget to run." So this store is a plain
# ! dict in memory. A restart drops every live link. That is correct, not a
# ! bug: a worker who loses a link starts the bot again, and nothing about her
# ! survives on our disk. The Telegram file upload is still sent alongside, so
# ! a restart never leaves her with nothing.
#
# ! NO PII, same as the pack itself — there is no name, phone or Aadhaar field
# ! anywhere in this project. We also do not record which token was opened,
# ! when, or by whom. A link is not an analytics event.
#
# * Stdlib only, like everything else here.
"""

import html
import json
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# * One hour. Long enough to walk somewhere and show it; short enough that a
# * forwarded link is stale before it travels.
TTL_SECONDS = 3600

# ! A public URL and finite RAM. Without a cap, a busy day (or someone driving
# ! the bot in a loop) grows this dict until the box dies. 500 live packs at
# ! ~10 KB each is about 5 MB, which a t4g.micro can hold without noticing.
MAX_LIVE = 500

_packs: dict[str, tuple[bytes, float]] = {}
_lock = threading.Lock()


def _sweep(now: float) -> None:
    """Drop expired entries. Caller holds the lock.

    # * Lazy, on every publish. No background thread and no cron — nothing to
    # * forget to start, and nothing that keeps running after the bot stops.
    """
    for token in [t for t, (_, expiry) in _packs.items() if expiry <= now]:
        del _packs[token]


def publish(blob: bytes, ttl: int = TTL_SECONDS) -> str:
    """Store one pack and return the token that reaches it."""
    now = time.time()
    with _lock:
        _sweep(now)
        # ! If the sweep did not free enough, evict the entries closest to
        # ! expiring. Dropping the oldest is right: it has been readable the
        # ! longest, so it is the one most likely already used.
        while len(_packs) >= MAX_LIVE:
            oldest = min(_packs, key=lambda t: _packs[t][1])
            del _packs[oldest]
        # * 16 bytes is 128 bits of entropy. Guessing one is not a threat model
        # * anyone can act on, and the URL still fits on a phone screen.
        token = secrets.token_urlsafe(16)
        _packs[token] = (blob, now + ttl)
        return token


def fetch(token: str) -> bytes | None:
    """Return the pack, or None if the token is unknown or expired."""
    with _lock:
        entry = _packs.get(token)
        if entry is None:
            return None
        blob, expiry = entry
        if expiry <= time.time():
            del _packs[token]
            return None
        return blob


def revoke(token: str) -> bool:
    """Forget one pack. Returns whether it was there.

    # ! /clear deletes the messages in the chat. A link left readable after
    # ! that would defeat the whole point of the command — the worker asked for
    # ! it to be gone, and a link is the part that outlives the chat.
    """
    with _lock:
        return _packs.pop(token, None) is not None


def live_count() -> int:
    """How many packs are readable right now. For tests and the startup line."""
    with _lock:
        _sweep(time.time())
        return len(_packs)


def clear() -> None:
    """Drop everything. Tests only."""
    with _lock:
        _packs.clear()


# * ---------------------------------------------------------------- serving


def base_url() -> str:
    """Where the worker reaches this server, e.g. https://host.example.

    # ! Empty means links are switched off and the channel falls back to
    # ! sending the file. That is deliberate: a link to a host that is not
    # ! actually reachable is worse than no link, and a developer running this
    # ! on a laptop has no such host.
    """
    return os.environ.get("PACK_BASE_URL", "").rstrip("/")


def url_for(token: str) -> str:
    return f"{base_url()}/p/{token}"


def _expired_page() -> bytes:
    """One page, both languages — we do not know which she chose an hour ago."""
    from sathi.core.content import s as _s

    bot = os.environ.get("BOT_URL", "https://t.me/YojanaSathiBot")
    blocks = []
    for lang in ("hi", "en"):
        body = html.escape(_s("link.expired_body", lang)).replace("\n", "<br>")
        blocks.append(
            f"<section lang='{lang}'>"
            f"<h1>{html.escape(_s('link.expired_title', lang))}</h1>"
            f"<p>{body}</p>"
            f"<p><a href='{html.escape(bot, quote=True)}'>"
            f"{html.escape(_s('link.expired_cta', lang))}</a></p></section>")
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<meta name='robots' content='noindex'>"
        "<title>" + html.escape(_s("link.expired_title", "en")) + "</title><style>"
        "body{font-family:system-ui,'Noto Sans Devanagari',sans-serif;line-height:1.7;"
        "max-width:34rem;margin:2rem auto;padding:0 1rem;color:#111}"
        "h1{font-size:1.25rem}section+section{border-top:1px solid #ccc;margin-top:2rem;"
        "padding-top:1rem}a{color:#2d5016}"
        "</style></head><body>" + "".join(blocks) + "</body></html>"
    ).encode("utf-8")


# * ------------------------------------------------------------ live numbers

# ! A public endpoint reading SQLite on every request is a free way to make the
# ! box slow. Sixty seconds is far fresher than anyone needs a counter to be.
_STATS_TTL = 60
_stats_cache: tuple[float, bytes] = (0.0, b"")

# ! ONLY these keys leave the box. by_source, by_purpose, the band
# ! distributions and anything per-session stay inside — they are the shape of
# ! who used it, and this endpoint answers strangers.
STATS_KEYS = ("screened", "packs", "unique_people", "schemes", "updated")


def stats_json(db_path: str = "", schemes: int = 0) -> bytes:
    """The whitelisted aggregates, cached. Empty JSON object on any failure."""
    global _stats_cache
    now = time.time()
    cached_at, body = _stats_cache
    if body and now - cached_at < _STATS_TTL:
        return body

    import sqlite3
    from datetime import datetime, timezone

    db_path = db_path or os.environ.get("DB_PATH", "")
    data: dict[str, object] = {}
    if db_path:
        try:
            from sathi.metrics import report

            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            try:
                counted = report.numbers(conn)
                data = {
                    "screened": counted["screened"],
                    "packs": counted["packs"],
                    "unique_people": report._reach(conn)["unique_people"],
                    "schemes": schemes or int(os.environ.get("SCHEME_COUNT", "0")),
                    "updated": datetime.now(timezone.utc).replace(
                        microsecond=0).isoformat().replace("+00:00", "Z"),
                }
            finally:
                conn.close()
        except Exception as e:  # noqa: BLE001 — a counter must never break the bot
            print(f"[links] stats unavailable: {type(e).__name__}")
            data = {}

    # ! Whitelist on the way OUT as well as the way in. If report.numbers()
    # ! ever grows a key, it does not silently become public.
    body = json.dumps({k: v for k, v in data.items() if k in STATS_KEYS}).encode("utf-8")
    _stats_cache = (now, body)
    return body


def handler_class() -> type[BaseHTTPRequestHandler]:
    """GET /p/<token>. Nothing else, on purpose."""

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def setup(self) -> None:
            self.request.settimeout(5)
            super().setup()

        def _respond(self, status: int, body: bytes, content_type: str,
                     extra: dict[str, str] | None = None) -> None:
            self.close_connection = True
            self.send_response(status)
            self.send_header("connection", "close")
            self.send_header("content-type", content_type)
            self.send_header("content-length", str(len(body)))
            # ! A pack is one worker's sheet. Keep it out of search engines, out
            # ! of caches, and out of the referer of anything she taps next.
            self.send_header("x-robots-tag", "noindex, nofollow")
            # ! Let a caller override rather than append. Sending both
            # ! "no-store" and "public, max-age=60" leaves the browser to pick,
            # ! which makes the cache promise meaningless.
            extra = extra or {}
            if "cache-control" not in extra:
                self.send_header("cache-control", "no-store")
            self.send_header("referrer-policy", "no-referrer")
            for name, value in extra.items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 — BaseHTTPRequestHandler's naming
            path = self.path.split("?", 1)[0].split("#", 1)[0]
            if path == "/stats.json":
                self._respond(200, stats_json(), "application/json; charset=utf-8",
                              extra={
                                  # ! Named origin, not "*". The landing page is
                                  # ! the only thing meant to read this.
                                  "access-control-allow-origin": os.environ.get(
                                      "STATS_ORIGIN", "https://avinashnegi1999.github.io"),
                                  "cache-control": f"public, max-age={_STATS_TTL}",
                              })
                return
            token = path[3:] if path.startswith("/p/") else ""
            blob = fetch(token) if token else None
            if blob is None:
                # ! 410, not 404. The link WAS valid; it aged out. A 404 reads
                # ! as "you typed it wrong" and sends her looking for a typo
                # ! that is not there.
                self._respond(410, _expired_page(), "text/html; charset=utf-8")
                return
            self._respond(200, blob, "text/html; charset=utf-8")

        def log_message(self, *args) -> None:
            # ! Silence, deliberately. The default access log records the path,
            # ! which is the token, and the client address. Logging which pack
            # ! was opened from where is exactly the per-person analytics this
            # ! project promises not to keep.
            pass

    return Handler


def serve_in_background(port: int | None = None) -> ThreadingHTTPServer | None:
    """Start the link server on loopback. Returns None when links are off."""
    if not base_url():
        return None
    port = int(os.environ.get("PACK_PORT", "8081")) if port is None else port
    # ! Loopback only, plain HTTP. TLS is Caddy's job, exactly as the WhatsApp
    # ! webhook does it — see deploy/RUNBOOK.md.
    host = os.environ.get("PACK_BIND", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), handler_class())
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True,
                     name="sathi-links").start()
    print(f"[links] serving packs on {host}:{server.server_address[1]} "
          f"as {base_url()}/p/<token>")
    return server


def _self_check() -> None:
    from pathlib import Path

    clear()

    token = publish(b"<html>hello</html>")
    assert fetch(token) == b"<html>hello</html>"
    assert fetch("not-a-token") is None

    # An expired token reads as gone AND stops occupying memory.
    stale = publish(b"old", ttl=-1)
    assert fetch(stale) is None
    assert stale not in _packs, "expired pack still held in memory"

    # /clear must be able to take a link back.
    revocable = publish(b"gone")
    assert revoke(revocable) is True
    assert fetch(revocable) is None
    assert revoke(revocable) is False, "revoking twice should report nothing to do"

    # ! The cap is the whole reason this is safe to expose publicly. Publish
    # ! well past it and the dict must not grow.
    clear()
    for i in range(MAX_LIVE + 50):
        publish(f"pack {i}".encode())
    assert len(_packs) <= MAX_LIVE, f"store grew to {len(_packs)}, cap is {MAX_LIVE}"
    # The most recent publish always survives eviction — otherwise a worker
    # could be handed a link that was dead before she read it.
    assert fetch(publish(b"newest")) == b"newest"

    # Tokens are unguessable and unique.
    clear()
    tokens = {publish(b"x") for _ in range(200)}
    assert len(tokens) == 200, "token collision"
    assert all(len(t) >= 20 for t in tokens)

    # ---- the served surface
    clear()
    import urllib.error
    import urllib.request

    os.environ["PACK_BASE_URL"] = "https://example.test"
    server = serve_in_background(port=0)
    assert server is not None
    root = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        good = publish(b"<html>sheet</html>")
        with urllib.request.urlopen(f"{root}/p/{good}", timeout=5) as r:
            assert r.status == 200
            assert r.read() == b"<html>sheet</html>"
            assert r.headers["cache-control"] == "no-store"
            assert "noindex" in r.headers["x-robots-tag"]

        for path in (f"/p/{publish(b'x', ttl=-1)}", "/p/nope", "/", "/p/"):
            try:
                urllib.request.urlopen(f"{root}{path}", timeout=5)
                raise AssertionError(f"{path} should not have returned 200")
            except urllib.error.HTTPError as e:
                assert e.code == 410, f"{path} returned {e.code}, wanted 410"
                page = e.read()
                assert b"noindex" in page
                # Both languages, because we cannot know which she picked.
                assert b"lang='hi'" in page and b"lang='en'" in page

        # ! A revoked token must be gone from the SERVER too, not just the dict
        # ! — /clear promises the sheet stops being readable.
        revoked = publish(b"secret")
        revoke(revoked)
        try:
            urllib.request.urlopen(f"{root}/p/{revoked}", timeout=5)
            raise AssertionError("revoked pack still served")
        except urllib.error.HTTPError as e:
            assert e.code == 410
    finally:
        server.shutdown()
        server.server_close()
        del os.environ["PACK_BASE_URL"]

    # ---- /stats.json: the whitelist is the whole safety story here
    clear()
    import sqlite3 as _sq
    import tempfile

    os.environ["PACK_BASE_URL"] = "https://example.test"
    fd, dbfile = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        conn = _sq.connect(dbfile)
        conn.executescript(
            (Path(__file__).resolve().parents[1] / "metrics" / "schema.sql").read_text())
        conn.execute("INSERT INTO reach (anon_id, channel, source, first_seen)"
                     " VALUES ('a', 'telegram', 'reddit', '2026-09-10T00:00:00')")
        conn.execute("INSERT INTO events (event_id, ts, session_id, channel,"
                     " event_type) VALUES ('e1', '2026-09-10T00:00:00', 's1',"
                     " 'telegram', 'eligibility_evaluated')")
        conn.commit()
        conn.close()

        global _stats_cache
        _stats_cache = (0.0, b"")
        payload = json.loads(stats_json(db_path=dbfile, schemes=7))
        assert payload["screened"] == 1, payload
        assert payload["unique_people"] == 1, payload
        assert payload["schemes"] == 7, payload
        assert payload["updated"].endswith("Z"), payload
        # ! The source a person came from is OURS, not the internet's. If this
        # ! ever leaks, the endpoint stops being an aggregate and starts being
        # ! a description of who used the bot.
        assert set(payload) <= set(STATS_KEYS), f"leaked keys: {set(payload) - set(STATS_KEYS)}"
        for banned in ("by_source", "by_purpose", "session_id", "distribution",
                       "reddit", "anon_id"):
            assert banned not in json.dumps(payload), f"{banned} reached the wire"

        # Cached: a second call must not re-read the database at all. Point it
        # at a path that does not exist — a cache miss would raise or return {}.
        assert json.loads(stats_json(db_path="/nonexistent/sathi.db"))["screened"] == 1,             "the 60s cache did not hold"

        # A broken database is a missing counter, never a crash and never a zero
        # presented as a real number.
        _stats_cache = (0.0, b"")
        assert json.loads(stats_json(db_path="/nonexistent/sathi.db")) == {}
    finally:
        try:
            os.remove(dbfile)
        except OSError:
            pass  # * Windows holds the sqlite handle until it is collected.
        del os.environ["PACK_BASE_URL"]
        _stats_cache = (0.0, b"")

    # Links off means off — no server, and the channel keeps sending the file.
    assert serve_in_background(port=0) is None
    assert base_url() == "" and url_for("t") == "/p/t"

    clear()
    print("pack.links self-check passed")


if __name__ == "__main__":
    _self_check()
