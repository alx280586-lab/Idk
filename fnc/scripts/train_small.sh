#!/usr/bin/env bash
set -euo pipefail

ARGS=("$@")
if [[ " ${ARGS[*]} " != *" --config "* && " ${ARGS[*]} " != *" -c "* ]]; then
  ARGS=(--config fnc/configs/simple_base.yaml "${ARGS[@]}")
fi

python -m fnc.training.cli stage1 "${ARGS[@]}"
