#!/usr/bin/env bash
# Build the ACT-GUI image from the ACT commit pinned in fixtures/catalog.json.
#   scripts/docker_build.sh                  # ACT from $ACT_SOURCE (default: $ACT_ROOT or /data1/guanqin/ACT)
#   ACT_SOURCE=https://github.com/<org>/ACT.git scripts/docker_build.sh
# Extra arguments are passed to "docker compose build".
set -euo pipefail
cd "$(dirname "$0")/.."

ACT_SOURCE="${ACT_SOURCE:-${ACT_ROOT:-/data1/guanqin/ACT}}"
COMMIT="$(python3 -c 'import json; print(json.load(open("fixtures/catalog.json"))["act"]["commit"])')"
STAGE=build/act

# Shallow checkout of exactly the pinned commit, with .git kept so the engine probe can verify it.
rm -rf "$STAGE"
git init -q "$STAGE"
git -C "$STAGE" fetch -q --depth 1 \
  --upload-pack="git -c uploadpack.allowAnySHA1InWant=true upload-pack" "$ACT_SOURCE" "$COMMIT"
git -C "$STAGE" -c advice.detachedHead=false checkout -q FETCH_HEAD
[ "$(git -C "$STAGE" rev-parse HEAD)" = "$COMMIT" ] || { echo "staged ACT is not $COMMIT" >&2; exit 1; }
echo "Staged ACT $COMMIT from $ACT_SOURCE"

docker compose build "$@"
