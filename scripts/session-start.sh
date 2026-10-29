#!/bin/bash
# SessionStart hook (wired in .claude/settings.json). Runs on every session start/resume,
# locally and in the cloud. Must be fast and idempotent.
set -u
cd "$CLAUDE_PROJECT_DIR" || exit 0

# 1. Upstream solver source (submodule). Shallow, only if missing.
if [ -f .gitmodules ] && [ ! -e upstream/.git ]; then
  git submodule update --init --depth 1 upstream >/tmp/submodule.log 2>&1 \
    || echo "WARN: submodule init failed — see /tmp/submodule.log" >&2
fi

# 2. Our tooling, editable install, skipped when pyproject is unchanged.
if [ -f tools/pyproject.toml ]; then
  stamp=.cache/pyproject.sha256
  mkdir -p .cache
  if ! sha256sum --check --status "$stamp" 2>/dev/null; then
    rm -f "$stamp"
    pip install -q --break-system-packages -e "tools[dev]" >/tmp/pip-tools.log 2>&1 \
      && sha256sum tools/pyproject.toml > "$stamp" \
      || echo "WARN: pip install -e tools failed — see /tmp/pip-tools.log" >&2
  fi
fi

# 3. Cloud only: make sure Docker is up and the solver image is present (pull in background).
if [ "${CLAUDE_CODE_REMOTE:-}" = "true" ]; then
  docker info >/dev/null 2>&1 || (dockerd >/tmp/dockerd.log 2>&1 &)
  IMG="$(grep -v '^#' CONTAINER_IMAGE 2>/dev/null | tr -d '[:space:]')"  # ADR-011
  ( sleep 3; [ -n "$IMG" ] && { docker image inspect "$IMG" >/dev/null 2>&1 || docker pull -q "$IMG" >/tmp/docker-pull.log 2>&1; } ) &
fi

# 4. One-line orientation for the agent.
[ -f UPSTREAM_VERSION ] && echo "codeaster-en: upstream pinned to $(grep -v '^#' UPSTREAM_VERSION | head -1)"
exit 0
