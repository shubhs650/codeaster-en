#!/bin/bash
# Build the codeaster-en wheel and sdist, install the wheel in a clean venv, and use it from
# outside the checkout (task 6.2, ADR-020). Run by the `package` job of .github/workflows/ci.yml.
# Usage: scripts/check-wheel.sh [dist-dir]     (default: dist/; nothing is published)
#
# Checks: the wheel is built from the sdist (python -m build), so the sdist carries the data;
# the installed package resolves its data inside site-packages, not the checkout; the gettext
# .mo loads; and `caen report` on the solid_static fixture reproduces the golden report.md.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$(realpath -m "${1:-$ROOT/dist}")"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

rm -rf "$DIST"
python -m build --outdir "$DIST" "$ROOT/tools"
python -m venv "$WORK/venv"
"$WORK/venv/bin/pip" install --quiet "$DIST"/codeaster_en-*.whl

cp -r "$ROOT/tests/fixtures/solid_static" "$WORK/job"
rm -rf "$WORK/job/report"
cd "$WORK"
"$WORK/venv/bin/python" - <<'PY'
import gettext
from pathlib import Path

import codeaster_en
from codeaster_en import comm, data, mess, report, results  # noqa: F401

site = Path(codeaster_en.__file__).parent
assert data.root() == site / "_data", data.root()
assert codeaster_en.__version__.startswith(data.upstream_version() + "."), codeaster_en.__version__
assert comm.load_command("AFFE_MODELE").name == "AFFE_MODELE"
catalog = gettext.translation("aster_messages", str(data.localedir()), languages=["en"])
assert len(catalog._catalog) > 6000, len(catalog._catalog)
print(f"codeaster-en {codeaster_en.__version__}: data in {data.root()}, {len(catalog._catalog)} .mo entries")
PY
"$WORK/venv/bin/caen" --version
"$WORK/venv/bin/caen" mess translate job/output/run.mess
"$WORK/venv/bin/caen" report job --no-pdf
diff "$ROOT/tests/golden/report/solid_static/report.md" job/report/report.md
echo "check-wheel: OK ($(ls "$DIST"))"
