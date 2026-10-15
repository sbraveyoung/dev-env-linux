#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export REPO_ROOT
CACHE_FILE="${REPO_ROOT}/.$(basename "${REPO_ROOT}")"
export CACHE_FILE
source "${REPO_ROOT}/scripts/cli.sh"
parse_cli "$@"

if [[ "$SHOW_HELP" == true ]]; then
  print_usage
  exit 0
fi
if [[ "$CLEAN_CACHE" == true ]]; then
  rm -f -- "$CACHE_FILE"
  exit 0
fi
SYSTEM=$(uname -s | tr 'A-Z' 'a-z')
export SYSTEM
if [[ $SYSTEM == darwin && $WITH_LINUX != false ]]; then
  source "${REPO_ROOT}/scripts/setup_linux_${WITH_LINUX}.sh"
  exit $?
fi

if [[ ${BASH_VERSINFO[0]} -lt 4 ]]; then
  printf 'Installation requires Bash 4+; current Bash is %s.\n' "$BASH_VERSION" >&2
  exit 2
fi

declare -A APP_FLAGS
if [[ ${#APP_FLAG_ARGS[@]} -gt 0 ]]; then
  for app_flag in "${APP_FLAG_ARGS[@]}"; do
    app=${app_flag%%=*}
    value=${app_flag#*=}
    APP_FLAGS[$app]="${APP_FLAGS[$app]:-}/${value}"
  done
fi
export APP_FLAGS OPTIONAL WITH_LINUX LINUX_ENV_NAME LINUX_USER
export LINUX_NORMAL_PASSWD LINUX_ROOT_PASSWD OPERATOR CONCURRENT TIMEOUT
export ENABLE_APPS DISABLE_APPS ONLY_APPS SKIP_SYSTEM
cd "${REPO_ROOT}/scripts"
source ./common_defines.sh
if is_mac; then
  source ./setup_macos.sh
elif is_linux; then
  source ./setup_linux.sh
else
  printf2stderr "error" "unsupported system:%s.\n" "$(uname -s)"
  exit 1
fi
