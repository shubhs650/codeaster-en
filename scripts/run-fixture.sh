#!/bin/bash
# Run one fixture case with the pinned code_aster container image.
# Usage: scripts/run-fixture.sh tests/fixtures/solid_static
# Works in a Claude Code cloud session (Docker is pre-installed) and in CI.
# Expects <case>/input/run.export referencing files relative to input/.
#
# The image comes from CONTAINER_IMAGE at the repo root (one line, `repo:tag@sha256:...`).
# There is no official image for the pinned upstream tag; see ADR-011 in docs/DECISIONS.md.
# Override with FIXTURE_IMAGE=... for experiments.
#
# FIXTURE_LANG=EN runs the same input with our English gettext catalog (task 3.4, ADR-004,
# docs/ENGLISH-LOCALE.md) and writes to <case>/output_en/ instead of output/: the .mo is built
# from en/messages, mounted at <install>/share/locale/aster (profile.sh resets ASTER_LOCALEDIR
# to that path, so -e ASTER_LOCALEDIR has no effect), and LANG="EN" is added to the DEBUT call
# of a copy of run.comm (the committed input is not changed).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CASE="${1:?usage: run-fixture.sh <fixture-dir>}"
CASE="$(cd "$CASE" && pwd)"
IMG="${FIXTURE_IMAGE:-$(grep -v '^#' "$ROOT/CONTAINER_IMAGE" | tr -d '[:space:]')}"

LANG_EN="${FIXTURE_LANG:-}"
case "$LANG_EN" in
  "") OUT="$CASE/output" ;;
  EN) OUT="$CASE/output_en" ;;
  *) echo "FIXTURE_LANG must be empty or EN, got '$LANG_EN'" >&2; exit 2 ;;
esac

# Start from an empty output directory so no file from an earlier run is committed by mistake.
rm -rf "$OUT"
mkdir -p "$OUT/tables"
docker image inspect "$IMG" >/dev/null 2>&1 || docker pull -q "$IMG"

INPUT="$CASE/input"
EXTRA=()
if [ "$LANG_EN" = EN ]; then
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  PYTHONPATH="$ROOT/tools${PYTHONPATH:+:$PYTHONPATH}" python3 -m codeaster_en translate gettext \
    --po "$TMP/aster_messages.po" --mo "$TMP/locale"
  cp -r "$CASE/input" "$TMP/input"
  grep -q '^DEBUT(' "$TMP/input/run.comm" || { echo "no DEBUT( line in run.comm" >&2; exit 2; }
  sed -i '0,/^DEBUT(/s//DEBUT(LANG="EN", /' "$TMP/input/run.comm"
  INPUT="$TMP/input"
  # The install prefix is the default RUNASTER_ROOT in the image's profile.sh.
  PREFIX="$(docker run --rm "$IMG" bash -c 'source /opt/activate.sh && sed -n "s/^: \${RUNASTER_ROOT:=\(.*\)}$/\1/p" "$(dirname "$(command -v run_aster)")/../share/aster/profile.sh"')"
  [ -n "$PREFIX" ] || { echo "cannot find the install prefix in the image" >&2; exit 2; }
  EXTRA=(-v "$TMP/locale:$PREFIX/share/locale/aster:ro")
fi

# The image's default user is uid 1000 and the solver is a Spack install activated by
# /opt/activate.sh. Run as the caller's uid so output/ stays writable and owned by the caller.
set +e
timeout "${FIXTURE_TIMEOUT:-1500}" docker run --rm \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$INPUT:/work/input:ro" -v "$OUT:/work/output" "${EXTRA[@]}" \
  -w /work/input "$IMG" \
  bash -c 'source /opt/activate.sh && run_aster run.export' > "$OUT/run_aster.stdout" 2>&1
rc=$?
set -e
echo "$rc" > "$OUT/exit_code"
PO_SHA=""
if [ "$LANG_EN" = EN ]; then
  # Results are the French run's; the English run is kept for its log only.
  rm -f "$OUT"/*.rmed
  PO_SHA="$(sha256sum "$TMP/aster_messages.po" | cut -d' ' -f1)"
fi

# Provenance of the outputs (CLAUDE.md rule 5): image, solver version, upstream pin, date.
DIGEST="$(docker image inspect "$IMG" --format '{{index .RepoDigests 0}}' 2>/dev/null || echo unknown)"
VERSION="$(docker run --rm "$IMG" bash -c 'source /opt/activate.sh && run_aster --version' 2>/dev/null | head -1)"
cat > "$OUT/provenance.json" <<JSON
{
  "case": "$(basename "$CASE")",
  "image": "$IMG",
  "image_digest": "$DIGEST",
  "solver_version": "$VERSION",
  "upstream_version": "$(grep -v '^#' "$ROOT/UPSTREAM_VERSION" | head -1 | tr -d '[:space:]')",
  "run_by": "${FIXTURE_RUN_BY:-scripts/run-fixture.sh}",
  "lang": "${LANG_EN:-FR}",
  "po_sha256": "$PO_SHA",
  "date_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "exit_code": $rc
}
JSON
echo "fixture $(basename "$CASE")${LANG_EN:+ ($LANG_EN)}: exit $rc (outputs in $OUT)"
exit 0
