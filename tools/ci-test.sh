#!/usr/bin/env bash

# Simulate GitHub Pages CI locally: build into a subfolder and
# run htmlproofer against that subfolder (mirrors pages.outputs.base_path)
#
# Usage:
#   bash tools/ci-test.sh                 # builds to _site/sim and runs htmlproofer there
#   bash tools/ci-test.sh -b "/mybase"    # builds to _site/mybase
#   bash tools/ci-test.sh --base-path "/project"

set -eu

BASE_PATH="/sim" # default simulated base_path

help() {
  echo "Simulate GitHub Pages CI locally"
  echo
  echo "Options:"
  echo "  -b, --base-path  Set the simulated base_path (default: /sim)"
  echo "  -h, --help       Show this help"
}

while (($#)); do
  case "$1" in
  -b | --base-path)
    BASE_PATH="$2"
    shift 2
    ;;
  -h | --help)
    help
    exit 0
    ;;
  *)
    echo "> Unknown option: $1" >&2
    help
    exit 1
    ;;
  esac
done

DEST_DIR="_site${BASE_PATH}"

echo "> Building site to: ${DEST_DIR}"

# Clean target only (do not remove entire _site to preserve other runs)
if [[ -d "$DEST_DIR" ]]; then
  rm -rf "$DEST_DIR"
fi

# Build (do not alter baseurl; CI doesn't either — only destination path differs)
JEKYLL_ENV=production bundle exec jekyll b -d "$DEST_DIR"

echo "> Running htmlproofer on: ${DEST_DIR}"

bundle exec htmlproofer "$DEST_DIR" \
  --disable-external \
  --ignore-urls "/^http:\/\/127.0.0.1/,/^http:\/\/0.0.0.0/,/^http:\/\/localhost/"

echo "> CI simulation completed successfully."
