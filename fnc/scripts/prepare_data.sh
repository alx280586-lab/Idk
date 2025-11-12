#!/usr/bin/env bash
set -euo pipefail

OUTPUT_PATH=${1:-data/tiny_corpus.txt}
mkdir -p "$(dirname "$OUTPUT_PATH")"
cp fnc/data/tiny_corpus.txt "$OUTPUT_PATH"
echo "Seed corpus copied to $OUTPUT_PATH" > /dev/stderr
