#!/usr/bin/env bash
# Convenience wrapper — the real entrypoint is ../start.sh.
set -euo pipefail
cd "$(dirname "$0")/.."
exec bash start.sh
