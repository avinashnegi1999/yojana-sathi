#!/usr/bin/env python3
"""Run every self-check in the project. One command, no test framework.

    python3 check.py

# * Same pattern as the rest of the toolchain: asserts, plain functions, and a
# * non-zero exit code when something breaks. Nothing to install.
"""

import importlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# * Modules exposing a _self_check() run in-process. Order is dependency order,
# * so the first failure points at the lowest broken layer instead of at the
# * five things downstream of it.
SELF_CHECK_MODULES = [
    "sathi.core.profile",
    # ! The scheme loader was missing from this list for a long time — the one
    # ! module that decides whether a rule is trustworthy was the one module the
    # ! build gate never ran. It sits second because everything else reads it.
    "sathi.core.schemes",
    "sathi.core.content",
    "sathi.rules.operators",
    "sathi.rules.engine",
    "sathi.metrics.events",
    "sathi.metrics.report",
    "sathi.render.templates",
    "sathi.render.llm",
    "sathi.render.audio",
    "sathi.pack.checklist",
    "sathi.pack.pack",
    "sathi.conversation.consent",
    "sathi.conversation.flow",
    "sathi.channels.router",
    "sathi.channels.telegram",
    "sathi.channels.whatsapp",
    "sathi.preview",
    # ! The sign-off tool. It is the only writer of `verified_by`, so its own
    # ! checks — that a signature changes exactly two lines, and that an
    # ! assistant cannot produce one — belong in the build gate.
    "sathi.review",
    # ! Source drift. Its self-check is offline on purpose — the build gate
    # ! must not depend on a ministry's uptime. `python3 -m sathi.sources`
    # ! is the online part, run by a maintainer.
    "sathi.sources",
]


def main() -> int:
    # * Self-checks use repository-relative data; match the test subprocesses.
    os.chdir(ROOT)
    # * Hindi and rupee signs must survive redirected Windows consoles too.
    os.environ["PYTHONIOENCODING"] = "utf-8"
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    failures = []

    for name in SELF_CHECK_MODULES:
        try:
            importlib.import_module(name)._self_check()
        except Exception as e:  # noqa: BLE001 — a check runner reports, it does not raise
            failures.append(f"{name}: {e}")
            print(f"FAIL {name}: {e}")

    for path in sorted((ROOT / "tests").glob("test_*.py")):
        result = subprocess.run([sys.executable, str(path)], cwd=ROOT)
        if result.returncode != 0:
            failures.append(path.name)

    print()
    if failures:
        print(f"{len(failures)} check(s) FAILED: {', '.join(failures)}")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
