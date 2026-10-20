#!/usr/bin/env bash
#
# Build and check the site with the same steps CI runs:
# production build, htmlproofer, post linter.
#
# Usage: bash tools/check.sh [--external]
#   --external   also check external links (slow; the weekly CI job does this)

set -eu

SITE_DIR="_site"
external=false

help() {
  echo "Build and check the site (same steps as CI)"
  echo
  echo "Usage:"
  echo
  echo "   bash $0 [options]"
  echo
  echo "Options:"
  echo "     --external   Also check external links."
  echo "     -h, --help   Print this information."
}

while (($#)); do
  case "$1" in
  --external)
    external=true
    shift
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

cd "$(dirname "$0")/.."

echo "> Building site to ${SITE_DIR}"
rm -rf "$SITE_DIR"
JEKYLL_ENV=production bundle exec jekyll b -d "$SITE_DIR"

echo "> Running htmlproofer"
proofer_opts=(--ignore-urls "/^http:\/\/127.0.0.1/,/^http:\/\/0.0.0.0/,/^http:\/\/localhost/")
if ! $external; then
  proofer_opts+=(--disable-external)
fi
bundle exec htmlproofer "$SITE_DIR" "${proofer_opts[@]}"

echo "> Linting posts"
uv run --quiet tools/lint_posts.py

echo "> All checks passed."
