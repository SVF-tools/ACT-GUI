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

# Catalog models are generated, git-ignored ACT files: copy them from a local checkout, pinned by sha256.
ACT_NETS_FROM="${ACT_NETS_FROM:-${ACT_ROOT:-/data1/guanqin/ACT}}"
python3 - "$ACT_NETS_FROM" "$STAGE" <<'EOF'
import hashlib, json, shutil, sys
from pathlib import Path
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
for m in json.load(open("fixtures/catalog.json"))["models"]:
    f = src / m["act_path"]
    if not f.is_file():
        sys.exit(f"missing catalog model {f} (set ACT_NETS_FROM to an ACT checkout that has it)")
    if hashlib.sha256(f.read_bytes()).hexdigest() != m["sha256"]:
        sys.exit(f"{f} does not match the sha256 pinned in fixtures/catalog.json")
    (dst / m["act_path"]).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f, dst / m["act_path"])
    print("staged model", m["act_path"])
EOF

docker compose build "$@"
