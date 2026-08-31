"""Hindi audio notes — optional, pluggable, never required.

# ? The TTS engine is still an open decision (plan §"uncertain"): Bhashini is
# ? the government option and politically the right one but of unknown
# ? reliability; espeak-ng is offline and free but robotic; a paid API is fast
# ? to ship and costs money. Rather than bet, this module shells out to whatever
# ? TTS_CMD names, so swapping engines is an env change, not a code change.
#
# ! Audio is an ENHANCEMENT. Every message is sent as text first and the text
# ! alone must be complete: a worker on a 2G connection, or with TTS_CMD unset,
# ! loses nothing but the voice.
"""

import os
import shlex
import subprocess
import tempfile
from pathlib import Path

# * {text} and {out} are substituted. Example that works on this laptop today:
# *   TTS_CMD='espeak-ng -v hi -w {out} {text}'
_TIMEOUT_S = 20


def is_available() -> bool:
    return bool(os.environ.get("TTS_CMD"))


def synthesise(text: str, out_dir: str | Path | None = None) -> Path | None:
    """Render Hindi text to an audio file. Returns None if TTS is off or fails.

    The caller sends text regardless, so a None here degrades the message from
    "text + voice" to "text" — never to nothing.
    """
    cmd_template = os.environ.get("TTS_CMD")
    if not cmd_template or not text.strip():
        return None

    directory = Path(out_dir or tempfile.gettempdir())
    directory.mkdir(parents=True, exist_ok=True)
    out = directory / f"sathi_{abs(hash(text)) % 10**10}.wav"

    # ! Built as a list, never through a shell. The text is user-adjacent input
    # ! and a shell here would be a command-injection hole.
    parts = shlex.split(cmd_template)
    argv = [out.as_posix() if p == "{out}" else (text if p == "{text}" else p) for p in parts]
    try:
        proc = subprocess.run(argv, capture_output=True, timeout=_TIMEOUT_S, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    if proc.returncode != 0 or not out.exists() or out.stat().st_size == 0:
        return None
    return out


def _self_check() -> None:
    saved = os.environ.pop("TTS_CMD", None)
    try:
        assert not is_available()
        assert synthesise("नमस्ते") is None, "TTS off must degrade quietly to text-only"

        # * A command that exists everywhere, to prove the plumbing without
        # * depending on a TTS engine being installed on this machine.
        with tempfile.TemporaryDirectory() as d:
            os.environ["TTS_CMD"] = "cp /etc/hostname {out}"
            got = synthesise("नमस्ते", out_dir=d)
            assert got is not None and got.exists(), "plumbing should produce a file"

            os.environ["TTS_CMD"] = "definitely-not-installed-xyz {text} {out}"
            assert synthesise("नमस्ते", out_dir=d) is None, "missing binary must not raise"
    finally:
        os.environ.pop("TTS_CMD", None)
        if saved is not None:
            os.environ["TTS_CMD"] = saved
    print("audio.py OK")


if __name__ == "__main__":
    _self_check()
