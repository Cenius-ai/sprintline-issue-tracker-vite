"""Seed CLI for the Sprintline demo workspace.

Run from the backend directory::

    python3 -m seed

Idempotent: on an already-seeded database it reports and exits without touching
rows. It never starts the HTTP server.
"""

from __future__ import annotations

import sys

from app.db import SessionLocal, ensure_schema
from app.seed import describe_seed, run_seed


def main() -> int:
    ensure_schema()
    with SessionLocal() as session:
        summary = run_seed(session)
    print(describe_seed(summary), flush=True)
    print("[seed] demo login: cenius@cenius.ai / cenius", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
