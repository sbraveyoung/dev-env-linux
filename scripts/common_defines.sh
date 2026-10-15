#!/usr/bin/env bash

set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/../sheath" && pwd)/functions.sh"
export PATH="${BIN_PATH}:${HOME}/.cargo/bin:${PATH}"

# $1-: command to be executed and all of args
execute_if_not_success() {
  [[ $# -gt 0 ]] || return 2
  # Managed receipts own idempotency and link repair. A historical global
  # success must not prevent their metadata/command checks from running.
  if [[ $1 =~ ^install_(linux|darwin)_(.+)$ ]] && declare -p MANAGED_INSTALL_APPS >/dev/null 2>&1 &&
      [[ ${MANAGED_INSTALL_APPS[${BASH_REMATCH[2]}]:-false} == true ]]; then
    "$@"
    return $?
  fi
  if [[ ${OPERATOR:-install} != install ]]; then
    "$@"
    return $?
  fi
  local record_file=${CACHE_FILE} key status
  touch "${record_file}" || return $?

  # Keep existing no-argument and ordinary app-hook cache entries usable.
  # Other calls encode argument boundaries, including whitespace and empty args.
  if [[ $# -eq 1 ]]; then
    key=$1
  elif [[ $# -eq 2 && $1 =~ ^(preinstall|install|config|preupgrade|upgrade|preuninstall|uninstall)_(linux|darwin)_[[:alnum:]_.+-]+$ && $2 == /* && $2 != *[[:space:]]* ]]; then
    key="${1}_${2}"
  else
    printf -v key '%q ' "$@"
    key="v2:${key}"
  fi

  if grep -Fqx -- "${key}" "${record_file}"; then
    printf2stdout "info" "command was executed success, skip:%s\n" "${key}"
    return 0
  fi

  "$@"
  status=$?
  [[ ${status} -eq 0 ]] || return "${status}"
  printf '%s\n' "${key}" >>"${record_file}"
}

# $0: cmd: install
# $1: macos or linux
# $2: tmp_dir
# $3: app
install() {
  local status
  if command_exist "preinstall_$1_$3"; then
    (execute_if_not_success preinstall_"$1"_"$3" "$2")
    status=$?
    [[ ${status} -eq 0 ]] || return "${status}"
  fi

  if ! command_exist "install_$1_$3"; then
    printf2stderr "error" "%s install function of %s is not defined.\n" "$1" "$3"
    return 1
  fi
  (execute_if_not_success install_"$1"_"$3" "$2")
  status=$?
  [[ ${status} -eq 0 ]] || return "${status}"

  # configuration is unnecessary, try to invoke it.
  if command_exist "config_$1_$3"; then
    (execute_if_not_success config_"$1_$3" "$2")
  fi
}

# $0: cmd: upgrade
# $1: macos or linux
# $2: tmp_dir
# $3: app
upgrade() {
  local status
  if command_exist "preupgrade_$1_$3"; then
    (execute_if_not_success preupgrade_"$1"_"$3" "$2")
    status=$?
    [[ ${status} -eq 0 ]] || return "${status}"
  fi

  if ! command_exist "upgrade_$1_$3"; then
    printf2stderr "error" "%s upgrade function of %s is not defined.\n" "$1" "$3"
    return 1
  fi
  (execute_if_not_success upgrade_"$1"_"$3" "$2")
}

# $0: cmd: uninstall
# $1: macos or linux
# $2: tmp_dir
# $3: app
uninstall() {
  local status
  if command_exist "preuninstall_$1_$3"; then
    (execute_if_not_success preuninstall_"$1"_"$3" "$2")
    status=$?
    [[ ${status} -eq 0 ]] || return "${status}"
  fi

  if ! command_exist "uninstall_$1_$3"; then
    printf2stderr "error" "%s uninstall function of %s is not defined.\n" "$1" "$3"
    return 1
  fi
  (execute_if_not_success uninstall_"$1"_"$3" "$2")
  status=$?
  [[ ${status} -eq 0 ]] || return "${status}"
  invalidate_app_cache "$1" "$2" "$3"
}

rollback() {
  command_exist "rollback_$1_$3" || { printf 'rollback unsupported for %s\n' "$3" >&2; return 2; }
  "rollback_$1_$3" "$2" || return
  invalidate_app_cache "$1" "$2" "$3"
}

invalidate_app_cache() {
  [[ -f ${CACHE_FILE} ]] || return 0
  local hook key encoded temp status
  for hook in preinstall install config; do
    key="${hook}_${1}_${3}_${2}"
    printf -v encoded '%q ' "${hook}_${1}_${3}" "$2"
    temp=$(mktemp "${CACHE_FILE}.XXXXXX") || return
    if grep -Fvx -e "$key" -e "v2:${encoded}" "${CACHE_FILE}" >"$temp"; then
      :
    else
      status=$?
      if [[ $status -ne 1 ]]; then rm -f -- "$temp"; return "$status"; fi
    fi
    mv -- "$temp" "${CACHE_FILE}" || return
  done
}

# $1: concurrent
# $2-: need to be installed/upgraded/uninstalled apps
batch_wrapper() {
  batch "${CONCURRENT}" _batch_run_app "$@"
}

_batch_run_app() {
  run_with_timeout "${OPERATOR}" "${SYSTEM}" "${tmp_dir:-${CLONE_PATH}}" "$1"
}

# Reuse existing Git checkouts after validating their metadata.
# $1-(n-1): git url to be clone and git args
# $n(the last arg): local path
git_clone_nx() {
  [[ $# -ge 2 ]] || return 2
  local destination=${!#}
  if [[ -d "$destination" ]]; then
    [[ -e "$destination/.git" ]] || {
      printf 'clone destination exists but is not a Git repository: %s\n' "$destination" >&2
      return 1
    }
    return 0
  fi
  git clone "$@"
}

# Keep downloads atomic so a partial file is never reused after failure.
wget_nx() {
  [[ $# -ge 3 ]] || return 2
  local args=("$@") destination='' index temp status
  for ((index=0; index<$#; index++)); do
    if [[ ${args[index]} == -O && $((index+1)) -lt $# ]]; then
      destination=${args[index+1]}
      break
    fi
  done
  [[ -n "$destination" ]] || { printf 'wget_nx requires -O FILE\n' >&2; return 2; }
  [[ -s "$destination" ]] && return 0
  mkdir -p -- "$(dirname "$destination")" || return
  temp=$(mktemp "${destination}.part.XXXXXX") || return
  args[index+1]=$temp
  if command wget "${args[@]}" --no-verbose --timeout=30 --tries=2; then
    mv -- "$temp" "$destination"
  else
    status=$?
    rm -f -- "$temp"
    return "$status"
  fi
}

# Runs a function in its own process group; terminate its children on timeout.
run_with_timeout() (
  [[ $# -gt 0 ]] || return 2
  local limit=${TIMEOUT:-7200} task timer status=0 marker
  [[ "$limit" =~ ^[1-9][0-9]*$ ]] || return 2
  marker=$(mktemp -d) || return
  trap 'rm -rf -- "$marker"' EXIT
  mkfifo "$marker/timer" || return
  exec 9<>"$marker/timer"
  set -m
  "$@" &
  task=$!
  (
    if ! read -r -t "$limit" -u 9 && kill -0 "$task" 2>/dev/null; then
      touch "$marker/timeout"
      kill -TERM -- "-$task" 2>/dev/null || :
      read -r -t 1 -u 9 || :
      kill -KILL -- "-$task" 2>/dev/null || :
    fi
  ) &
  timer=$!
  if wait "$task"; then :; else status=$?; fi
  if [[ -f "$marker/timeout" ]]; then
    wait "$timer" 2>/dev/null || :
    status=124
    printf 'task timed out after %s seconds\n' "$limit" >&2
  else
    printf '\n' >&9
    wait "$timer" 2>/dev/null || :
  fi
  return "$status"
)

linux_arch() {
  case "$(uname -m)" in
    x86_64|amd64) printf 'amd64\n' ;;
    aarch64|arm64) printf 'arm64\n' ;;
    *) printf 'unsupported architecture\n' >&2; return 2 ;;
  esac
}
