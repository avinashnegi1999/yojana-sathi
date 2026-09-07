"""Entrypoint isolation checks, run by check.py; no deployment or real data.

# ! A renderer rehearsal must never contaminate the impact database.
"""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sathi import main


def test_preview_never_opens_the_impact_database():
    with patch.object(main, "startup_report"), patch.object(main, "EventLog") as database, \
            patch("sathi.preview.run", return_value=0):
        assert main.main(["--preview", "whatsapp"]) == 0
    assert not database.called


if __name__ == "__main__":
    test_preview_never_opens_the_impact_database()
    print("  ok  test_preview_never_opens_the_impact_database")
    print("test_entrypoint.py OK")
