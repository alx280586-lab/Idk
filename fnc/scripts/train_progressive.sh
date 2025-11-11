#!/usr/bin/env bash
set -euo pipefail

python -m fnc.training.cli progressive "$@"
