#!/usr/bin/env bash
set -euo pipefail

CONFIG=${1:-configs/ten_trillion.yaml}
OUTPUT=${2:-bundles/ten_trillion_untrained}

python -m fnc.training.cli init --config "${CONFIG}" --output "${OUTPUT}"
