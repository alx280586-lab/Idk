#!/usr/bin/env bash
set -euo pipefail

OUTPUT_PATH=${1:-data/base_corpus.txt}
SOURCE_PATH=${2:-fnc/data/base_corpus.txt}

if [[ ! -f "$SOURCE_PATH" ]]; then
  echo "Source corpus $SOURCE_PATH not found" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_PATH")"
cp "$SOURCE_PATH" "$OUTPUT_PATH"
echo "Seed corpus copied to $OUTPUT_PATH" >&2
