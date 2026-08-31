"""Optional LLM layer. Strictly outside the rule engine.

# ! The model does exactly two jobs here:
# !   1. Map free text to an occupation CODE — which is then confirmed by the
# !      worker before it enters the profile. A rejected guess is discarded.
# !   2. Rephrase Hindi a human authored, for a specific listener.
# ! It never sees a threshold, never produces a ₹ figure, never produces a
# ! verdict, and never answers a scheme question from its own knowledge.
#
# ! LLM_API_KEY unset is a TESTED configuration, not a degraded one. Every
# ! function here returns a safe value when the key is missing, and eligibility
# ! output is byte-identical either way — the engine never calls this module.
#
# * stdlib urllib on purpose. One POST to one endpoint does not justify a
# * dependency, and a container that installs nothing cannot fail to install.
"""

import json
import os
import re
import urllib.error
import urllib.request

from sathi.core.content import occupation_codes, occupations

_DEFAULT_URL = "https://api.anthropic.com/v1/messages"
_DEFAULT_MODEL = "claude-sonnet-5"
_TIMEOUT_S = 10
_DIGITS = re.compile(r"\d+")


def is_available() -> bool:
    return bool(os.environ.get("LLM_API_KEY"))


def _ask(system: str, user: str, max_tokens: int = 200) -> str | None:
    """One request. Any failure returns None — a session never dies on the LLM."""
    key = os.environ.get("LLM_API_KEY")
    if not key:
        return None
    body = json.dumps(
        {
            "model": os.environ.get("LLM_MODEL", _DEFAULT_MODEL),
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        os.environ.get("LLM_BASE_URL", _DEFAULT_URL),
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        parts = [b.get("text", "") for b in payload.get("content", []) if b.get("type") == "text"]
        return "".join(parts).strip() or None
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, OSError):
        # * Network down, bad key, rate limit, malformed reply — all the same
        # * thing from here: fall back to buttons. Never surface it to a worker.
        return None


_OCCUPATION_SYSTEM = """You map a worker's own description of their job to ONE code.
Reply with the code only — no punctuation, no explanation, no other words.
If nothing fits well, reply exactly: none
You are not deciding any benefit or eligibility. You are only labelling a job."""


def propose_occupation(said: str) -> str | None:
    """Suggest an occupation code for free text. ALWAYS confirmed by the worker.

    Returns None when the key is unset, the call fails, or the reply is not one
    of our codes. None means "show the menu" — never means "pick something".
    """
    if not said.strip() or not is_available():
        return None
    menu = "\n".join(f"{o.code}: {o.label_en} / {o.label_hi}" for o in occupations())
    reply = _ask(_OCCUPATION_SYSTEM, f"Codes:\n{menu}\n\nWorker said: {said}", max_tokens=20)
    if not reply:
        return None
    code = reply.strip().split()[0].strip(".,'\"")
    # ! Whitelist. A hallucinated code is discarded, not passed through.
    return code if code in occupation_codes() else None


_REPHRASE_SYSTEM = """Rewrite the Hindi below so a worker with little schooling
understands it easily. Keep every number, every rupee amount, every scheme name
and every meaning exactly as they are. Add nothing. Remove no fact. Do not
explain, do not advise, do not mention eligibility rules of your own.
Reply with the rewritten Hindi only."""


def rephrase(text: str, audience_hint: str = "") -> str:
    """Simplify authored Hindi. Returns the original on any doubt.

    # ! Guard, not trust: if the rewrite introduces a number the original did
    # ! not contain, it is discarded. That is the one failure mode that could
    # ! put a fabricated ₹ figure in front of a worker.
    """
    if not text.strip() or not is_available():
        return text
    user = f"{audience_hint}\n\n{text}".strip()
    out = _ask(_REPHRASE_SYSTEM, user, max_tokens=800)
    if not out:
        return text
    if set(_DIGITS.findall(out)) - set(_DIGITS.findall(text)):
        return text  # ! invented a number — throw the whole rewrite away
    return out


def _self_check() -> None:
    # * Runs with no key and no network: this IS the supported configuration.
    saved = os.environ.pop("LLM_API_KEY", None)
    try:
        assert not is_available()
        assert propose_occupation("मैं ईंट लगाता हूँ") is None
        assert rephrase("आपको ₹12,000 मिलेंगे") == "आपको ₹12,000 मिलेंगे"
        assert rephrase("") == ""

        # * The number guard, exercised without a network by faking one reply.
        import sys

        mod = sys.modules[__name__]  # * the running copy, not a second import

        os.environ["LLM_API_KEY"] = "test-not-a-real-key"
        real = mod._ask
        try:
            mod._ask = lambda *a, **k: "आपको ₹99,999 मिलेंगे"
            assert mod.rephrase("आपको ₹12,000 मिलेंगे") == "आपको ₹12,000 मिलेंगे", \
                "a rewrite that invents a number must be discarded"
            mod._ask = lambda *a, **k: "आपको बारह हज़ार रुपये मिलेंगे 12,000"
            assert "बारह" in mod.rephrase("आपको ₹12,000 मिलेंगे")
            mod._ask = lambda *a, **k: "construction"
            assert mod.propose_occupation("ईंट") == "construction"
            mod._ask = lambda *a, **k: "brick_layer_9000"
            assert mod.propose_occupation("ईंट") is None, "unknown code must be discarded"
        finally:
            mod._ask = real
            os.environ.pop("LLM_API_KEY", None)
    finally:
        if saved is not None:
            os.environ["LLM_API_KEY"] = saved
    print("llm.py OK")


if __name__ == "__main__":
    _self_check()
