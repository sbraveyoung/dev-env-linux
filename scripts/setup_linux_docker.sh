#!/usr/bin/env bash
set -euo pipefail
command -v docker >/dev/null || { printf 'Docker is required for --with-linux=docker\n' >&2; return 2; }
source "${REPO_ROOT}/scripts/forward_cli.sh"
make_linux_args
image="dev-env-linux/${LINUX_ENV_NAME}:latest"
docker build -t "$image" --build-arg "NORMAL_USER=$LINUX_USER" -f "$REPO_ROOT/scripts/dockerfile_ubuntu" "$REPO_ROOT"
if docker container inspect "$LINUX_ENV_NAME" >/dev/null 2>&1; then
  printf 'container already exists: %s (choose another --linux_env_name)\n' "$LINUX_ENV_NAME" >&2
  return 2
fi
# Keep the container available for development after the installation finishes.
docker run -d --name "$LINUX_ENV_NAME" "$image" sleep infinity
docker exec "$LINUX_ENV_NAME" bash ./build.sh "${LINUX_ARGS[@]}"
