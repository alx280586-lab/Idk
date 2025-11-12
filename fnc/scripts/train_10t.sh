#!/usr/bin/env bash
set -euo pipefail

CONFIG=${CONFIG:-configs/ten_trillion.yaml}
CHECKPOINT_DIR=${CHECKPOINT_DIR:-runs/ten_trillion}
STAGE1_STEPS=${STAGE1_STEPS:-50}
PROGRESSIVE_STEPS=${PROGRESSIVE_STEPS:-50}
DISTILL_STEPS=${DISTILL_STEPS:-50}

mkdir -p "${CHECKPOINT_DIR}"

python -m fnc.training.cli stage1 --config "${CONFIG}" --steps "${STAGE1_STEPS}" --checkpoint-dir "${CHECKPOINT_DIR}/stage1"
python -m fnc.training.cli progressive --config "${CONFIG}" --steps "${PROGRESSIVE_STEPS}" --checkpoint-dir "${CHECKPOINT_DIR}/stage2"
python -m fnc.training.cli distill --config "${CONFIG}" --steps "${DISTILL_STEPS}" --checkpoint-dir "${CHECKPOINT_DIR}/stage3"
