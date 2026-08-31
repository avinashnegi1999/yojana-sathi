# =====================================================================
# Scheme Sathi — deployable image
# =====================================================================
# ! Zero third-party dependencies, so there is no pip install step that can
# ! fail on deploy day. The image is the stdlib, the code, and the data files.
#
# ! DB_PATH must point at a MOUNTED VOLUME. Free-tier containers lose their
# ! ephemeral disk on restart, and a lost event log means every impact number
# ! in the submission is fiction. Verify this on deploy day, week 6.

FROM python:3.12-slim

# * No build tools, no compiler: nothing here compiles.
WORKDIR /app

COPY sathi/ ./sathi/
COPY data/ ./data/
COPY tests/ ./tests/
COPY check.py pyproject.toml ./

# ! The full suite runs at build time — self-checks AND tests, which is why
# ! tests/ is copied in. An image that cannot pass its own checks never reaches
# ! a worker.
RUN python3 check.py

ENV PYTHONUNBUFFERED=1 \
    DB_PATH=/data/sathi.db

VOLUME ["/data"]

# * Long polling: no inbound port, no public URL, no TLS termination needed.
CMD ["python3", "-m", "sathi.main", "--telegram"]
