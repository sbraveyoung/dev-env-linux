#!/usr/bin/env bash
set -euo pipefail
command -v orbctl >/dev/null || { printf 'OrbStack is required for --with-linux=vm\n' >&2; return 2; }
source "${REPO_ROOT}/scripts/forward_cli.sh"
make_linux_args
if ! orbctl info "$LINUX_ENV_NAME" >/dev/null 2>&1; then
  orbctl create --isolated --user "$LINUX_USER" ubuntu:24.04 "$LINUX_ENV_NAME"
fi
if [[ -n "$LINUX_NORMAL_PASSWD" ]]; then
  printf '%s:%s\n' "$LINUX_USER" "$LINUX_NORMAL_PASSWD" | orbctl run -m "$LINUX_ENV_NAME" -u root chpasswd
fi
if [[ -n "$LINUX_ROOT_PASSWD" ]]; then
  printf 'root:%s\n' "$LINUX_ROOT_PASSWD" | orbctl run -m "$LINUX_ENV_NAME" -u root chpasswd
fi
linux_home=$(orbctl run -m "$LINUX_ENV_NAME" -u "$LINUX_USER" printenv HOME)
linux_repo="$linux_home/dev-env-linux"
orbctl run -m "$LINUX_ENV_NAME" -u "$LINUX_USER" mkdir -p "$linux_repo"
# Isolated machines disable shared-folder push; stream a source-only archive.
tar -C "$REPO_ROOT" -czf - build.sh scripts sheath config tests |
  orbctl run -m "$LINUX_ENV_NAME" -u "$LINUX_USER" tar -xzf - -C "$linux_repo"
orbctl run -m "$LINUX_ENV_NAME" -u "$LINUX_USER" -w "$linux_repo" bash ./build.sh "${LINUX_ARGS[@]}"
