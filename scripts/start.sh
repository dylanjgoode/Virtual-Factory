#!/usr/bin/env bash
set -euo pipefail

docker compose up -d

export VF_BROKER_PORT="${VF_BROKER_PORT:-1884}"

PYTHON_BIN="python"
if [ -x ".venv/bin/python" ]; then
  PYTHON_BIN=".venv/bin/python"
fi

$PYTHON_BIN scripts/run_all.py "$@"
