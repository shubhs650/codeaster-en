#!/bin/bash
# Cloud ENVIRONMENT setup script for codeaster-en.
# Paste this into: claude.ai/code → environment selector → "codeaster-en" → Setup script.
# (It is kept in the repo only for reference/versioning; the environment does not read it from here.)
#
# Runs as root on Ubuntu 24.04 BEFORE Claude Code starts, once per environment cache (~7 days).
# Must exit 0 and should finish in < ~5 min, or the environment is not cached.
# Everything non-critical ends in `|| true` so a flaky mirror never blocks a session.

set -u
export DEBIAN_FRONTEND=noninteractive

# 1. System packages: PDF/text tools for doc ingestion, gettext for .po/.mo, HDF5 for MED, WeasyPrint deps.
( apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    gettext poppler-utils libhdf5-dev \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b fonts-dejavu-core \
  ) >/tmp/setup-apt.log 2>&1 || echo "apt step failed (non-fatal), see /tmp/setup-apt.log"

# 2. Python libraries used by tools/ (installed globally so every session has them without a venv).
#    The repo's own package is installed editable by the SessionStart hook, not here.
( pip install -q --break-system-packages \
    typer pyyaml jsonschema jinja2 weasyprint pymupdf pdfplumber \
    meshio h5py numpy pandas gmsh medcoupling \
  ) >/tmp/setup-pip.log 2>&1 || echo "pip step had failures (non-fatal), see /tmp/setup-pip.log"

# 3. Pre-pull the official code_aster solver image so fixture runs don't pay the pull each session.
#    The image is large; give it ~3 minutes. If it doesn't finish, the SessionStart hook pulls it later.
CA_IMAGE="${CODEASTER_IMAGE:-codeastersolver/codeaster-seq:latest}"
if ! docker info >/dev/null 2>&1; then
  (dockerd >/tmp/dockerd.log 2>&1 &) ; sleep 5
fi
timeout 180 docker pull -q "$CA_IMAGE" >/tmp/setup-docker.log 2>&1 || echo "docker pull not finished in setup (non-fatal)"

exit 0
