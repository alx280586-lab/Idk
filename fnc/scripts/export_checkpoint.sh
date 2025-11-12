#!/usr/bin/env bash
set -euo pipefail

SRC=${1:-runs/stage1/generator.pt}
DEST=${2:-artifacts/generator.pt}
mkdir -p "$(dirname "$DEST")"
cp "$SRC" "$DEST"
echo "Checkpoint exported to $DEST" > /dev/stderr
