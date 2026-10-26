#!/usr/bin/env bash
set -euo pipefail
command -v orbctl >/dev/null || { printf 'OrbStack is required for --with-linux=vm\n' >&2; return 2; }
source "${REPO_ROOT}/scripts/forward_cli.sh"
make_linux_args
if ! orbctl info "$LINUX_ENV_NAME" >/dev/null 2>&1; then
  orbctl create --isolated --user "$LINUX_USER" ubuntu:24.04 "$LINUX_ENV_NAME"
fi
# Source receipt validation needs Python before build.sh can bootstrap dependencies.
# The wrapper creates Ubuntu guests; bootstrap only inside that guest when needed.
if ! orbctl run -m "$LINUX_ENV_NAME" -u "$LINUX_USER" sh -c 'command -v python3' >/dev/null; then
  orbctl run -m "$LINUX_ENV_NAME" -u root apt-get update
  orbctl run -m "$LINUX_ENV_NAME" -u root env DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends python3
fi
if [[ -n "$LINUX_NORMAL_PASSWD" ]]; then
  printf '%s:%s\n' "$LINUX_USER" "$LINUX_NORMAL_PASSWD" | orbctl run -m "$LINUX_ENV_NAME" -u root chpasswd
fi
if [[ -n "$LINUX_ROOT_PASSWD" ]]; then
  printf 'root:%s\n' "$LINUX_ROOT_PASSWD" | orbctl run -m "$LINUX_ENV_NAME" -u root chpasswd
fi
linux_home=$(orbctl run -m "$LINUX_ENV_NAME" -u "$LINUX_USER" printenv HOME)
linux_repo="$linux_home/dev-env-linux"
# Execute the receiver in the guest; no project Python is run on the host.
# Do not replace receiver code in a possibly edited guest checkout to bootstrap it.
sync_code=$(cat "$REPO_ROOT/scripts/source_sync.py")
COPYFILE_DISABLE=1 tar -C "$REPO_ROOT" --exclude='__pycache__' --exclude='*.pyc' --exclude='._*' \
  -czf - build.sh software.lock.json scripts sheath config tests |
  orbctl run -m "$LINUX_ENV_NAME" -u "$LINUX_USER" python3 -c "$sync_code" "$linux_repo"
orbctl run -m "$LINUX_ENV_NAME" -u "$LINUX_USER" -w "$linux_repo" bash ./build.sh "${LINUX_ARGS[@]}"
