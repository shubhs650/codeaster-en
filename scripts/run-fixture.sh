#!/bin/bash
# Run one fixture case with the pinned code_aster container image.
# Usage: scripts/run-fixture.sh tests/fixtures/solid_static
# Works in a Claude Code cloud session (Docker is pre-installed) and in CI.
# Expects <case>/input/run.export referencing files relative to input/.
#
# The image comes from CONTAINER_IMAGE at the repo root (one line, `repo:tag@sha256:...`).
# There is no official image for the pinned upstream tag; see ADR-011 in docs/DECISIONS.md.
# Override with FIXTURE_IMAGE=... for experiments.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CASE="${1:?usage: run-fixture.sh <fixture-dir>}"
CASE="$(cd "$CASE" && pwd)"
IMG="${FIXTURE_IMAGE:-$(grep -v '^#' "$ROOT/CONTAINER_IMAGE" | tr -d '[:space:]')}"

# Start from an empty output/ so no file from an earlier run is committed by mistake.
rm -rf "$CASE/output"
mkdir -p "$CASE/output/tables"
docker image inspect "$IMG" >/dev/null 2>&1 || docker pull -q "$IMG"

# The image's default user is uid 1000 and the solver is a Spack install activated by
# /opt/activate.sh. Run as the caller's uid so output/ stays writable and owned by the caller.
set +e
timeout "${FIXTURE_TIMEOUT:-1500}" docker run --rm \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$CASE/input:/work/input:ro" -v "$CASE/output:/work/output" \
  -w /work/input "$IMG" \
  bash -c 'source /opt/activate.sh && run_aster run.export' > "$CASE/output/run_aster.stdout" 2>&1
rc=$?
set -e
echo "$rc" > "$CASE/output/exit_code"

# Provenance of the outputs (CLAUDE.md rule 5): image, solver version, upstream pin, date.
DIGEST="$(docker image inspect "$IMG" --format '{{index .RepoDigests 0}}' 2>/dev/null || echo unknown)"
VERSION="$(docker run --rm "$IMG" bash -c 'source /opt/activate.sh && run_aster --version' 2>/dev/null | head -1)"
cat > "$CASE/output/provenance.json" <<JSON
{
  "case": "$(basename "$CASE")",
  "image": "$IMG",
  "image_digest": "$DIGEST",
  "solver_version": "$VERSION",
  "upstream_version": "$(grep -v '^#' "$ROOT/UPSTREAM_VERSION" | head -1 | tr -d '[:space:]')",
  "run_by": "${FIXTURE_RUN_BY:-scripts/run-fixture.sh}",
  "date_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "exit_code": $rc
}
JSON
echo "fixture $(basename "$CASE"): exit $rc (outputs in $CASE/output)"
exit 0
