#!/bin/bash
# Run one fixture case with the official code_aster container.
# Usage: scripts/run-fixture.sh tests/fixtures/solid_static
# Works in a Claude Code cloud session (Docker is pre-installed) and in CI.
# Expects <case>/input/run.export referencing files relative to input/.
set -euo pipefail
CASE="${1:?usage: run-fixture.sh <fixture-dir>}"
CASE="$(cd "$CASE" && pwd)"
TAG="latest"; [ -f CONTAINER_TAG ] && TAG="$(tr -d '[:space:]' < CONTAINER_TAG)"
IMG="codeastersolver/codeaster-seq:${TAG}"

mkdir -p "$CASE/output"
docker image inspect "$IMG" >/dev/null 2>&1 || docker pull -q "$IMG"

set +e
timeout "${FIXTURE_TIMEOUT:-1500}" docker run --rm \
  -v "$CASE/input:/work/input:ro" -v "$CASE/output:/work/output" \
  -w /work/input "$IMG" \
  bash -lc 'run_aster run.export' > "$CASE/output/run_aster.stdout" 2>&1
rc=$?
set -e
echo "$rc" > "$CASE/output/exit_code"
echo "fixture $(basename "$CASE"): exit $rc (outputs in $CASE/output)"
exit 0
