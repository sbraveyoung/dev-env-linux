#!/usr/bin/env bash

#set -euo pipefail
set -uo pipefail

# direnv controls explicit authorization, parent-directory inheritance and unloading.
# A plain .env is never sourced by these navigation helpers.
scd() {
  [[ $# -le 1 ]] || return 2
  cd -- "${1:-$HOME}" || return
  if command -v direnv >/dev/null 2>&1; then
    local changes status=0
    changes=$(direnv export bash) || status=$?
    # A blocked .envrc can still emit the exports that unload the previous dir.
    eval "$changes" || return
    return "$status"
  fi
}

cdls() {
  scd "$@" || return
  if command -v eza >/dev/null 2>&1; then command eza --all
  elif command -v exa >/dev/null 2>&1; then command exa --all
  else command ls -a; fi
}

source "$(dirname "${BASH_SOURCE[0]}")/constant.sh"

parse_git_branch() {
	git branch 2>/dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ [\1]/'
}

echo_date() {
	date +'%Y/%m/%d %H:%M:%S'
}

echo_sentence() {
	local quo
	quo=$(fortune -s) || return
	printf '%s\n' "$quo"
	#echo `trans $quo` # toooooo slow!
}

save_origin_env() {
	[[ $# -eq 1 && $1 =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || return 2
	printf -v "ORIGIN_$1" '%s' "${!1}"
}

restore_origin_env() {
	[[ $# -eq 1 && $1 =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || return 2
	local origin_key="ORIGIN_$1"
	printf -v "$1" '%s' "${!origin_key}"
	unset "$origin_key"
}

smart_cp() {
	[[ $# -ge 2 ]] || return 2
	local destination=${!#} parent
	parent=$(dirname "$destination") || return
	command mkdir -p -- "$parent" || return
	command cp "$@"
}

# Append exact assignments once, without evaluating input as shell code.
save_env() {
	[[ $# -eq 2 && $2 =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]] || return 2
	local value line
	IFS= read -r -p "$1" value || return
	printf -v "$2" '%s' "$value"
	line="$2=$value"
	if [[ ! -f .env ]] || ! grep -Fqx -- "$line" .env; then
		printf '%s\n' "$line" >>.env
	fi
	return 0
}

# deprecated, for autojump
jls() {
	j "$1"
	exa --all
}

jcurl() {
	curl "$1" | jq
}

mkdir_and_cd() {
	[[ $# -gt 0 ]] || return 2
	command mkdir "$@" || return
	cd -- "${!#}" || return
}

every() {
	[[ $# -ge 2 && $1 =~ ^[0-9]+([.][0-9]+)?$ ]] || return 2
	local interval=$1
	shift
	while true; do
		"$@" || return
		sleep "$interval" || return
	done
}

echo_last_status() {
	[ "$1" -ne 0 ] && echo x || echo y
}

timestamp() {
	# GNU date（Linux）与 BSD date（macOS）语法不同，需做兼容处理：
	#   Linux: date --rfc-3339=s -d @<epoch>
	#   macOS: date -r <epoch> '+格式'
	if is_mac; then
		date -r "$1" '+%Y-%m-%d %H:%M:%S %z'
	else
		date --rfc-3339=s -d "@$1"
	fi
}

# A unique sibling directory reserves each version atomically; payload preserves
# the source name/type independently of timestamp parsing and symlink targets.
_backup_paths() {
  [[ $# -ge 2 ]] || return 2
  local operation=$1 origin parent backup
  shift
  for origin in "$@"; do
    [[ -e "$origin" || -L "$origin" ]] || { printf 'backup: missing path: %s\n' "$origin" >&2; return 1; }
  done
  for origin in "$@"; do
    origin=${origin%/}
    [[ -n "$origin" && ${origin##*/} != . && ${origin##*/} != .. ]] || return 2
    parent=$(cd -- "$(dirname -- "$origin")" && pwd -P) || return
    origin="$parent/$(basename -- "$origin")"
    backup=$(mktemp -d "$origin.bak.$(date -u +%Y%m%dT%H%M%S).XXXXXX") || return
    if [[ $operation == cp ]]; then command cp -a -- "$origin" "$backup/payload" || return
    else command mv -- "$origin" "$backup/payload" || return; fi
    printf '%s\n' "$backup"
  done
}

bak() { _backup_paths cp "$@"; }
mbak() { _backup_paths mv "$@"; }

_backup_same() {
  if [[ -L $1 || -L $2 ]]; then
    [[ -L $1 && -L $2 && $(readlink "$1") == "$(readlink "$2")" ]]
  elif [[ -d $1 && -d $2 ]]; then
    command diff -qr -- "$1" "$2" >/dev/null 2>&1
  elif [[ -f $1 && -f $2 ]]; then
    command cmp -s -- "$1" "$2"
  else return 1; fi
}

_restore_backups() {
  [[ $# -ge 2 ]] || return 2
  local operation=$1 backup origin payload container
  shift
  for backup in "$@"; do
    backup=${backup%/};container=false
    if [[ $backup =~ ^(.+)\.bak\.[0-9]{8}T[0-9]{6}\.[A-Za-z0-9]{6}$ && -d $backup && ! -L $backup ]]; then
      origin=${BASH_REMATCH[1]};payload="$backup/payload";container=true
    elif [[ $backup == *.bak ]]; then
      origin=${backup%.bak};payload=$backup
    else printf 'restore: invalid backup path: %s\n' "$backup" >&2; return 2; fi
    [[ -n $origin && ( -e $payload || -L $payload ) ]] || return 1
    if [[ -e $origin || -L $origin ]]; then
      if _backup_same "$payload" "$origin"; then
        if [[ $operation == mv ]]; then
          command rm -rf -- "$payload" || return
          [[ $container != true ]] || command rmdir -- "$backup" || return
        fi
        continue
      fi
      mbak "$origin" || return
    fi
    if [[ $operation == cp ]]; then command cp -a -- "$payload" "$origin" || return
    else command mv -- "$payload" "$origin" || return; fi
    if [[ $operation == mv && $container == true ]]; then command rmdir -- "$backup" || return; fi
  done
}

unbak() { _restore_backups cp "$@"; }
umbak() { _restore_backups mv "$@"; }

touchx() {
	touch -- "$1" && chmod +x -- "$1"
}

# LOG_LEVEL defaults to trace for compatibility; quiet suppresses ordinary output.
_log_rank() {
  case "$1" in
    quiet) printf 0 ;; panic) printf 1 ;; fatal) printf 2 ;; error) printf 3 ;;
    warning) printf 4 ;; info) printf 5 ;; verbose) printf 6 ;; debug) printf 7 ;; trace) printf 8 ;;
    *) printf 'invalid log level: %s\n' "$1" >&2; return 2 ;;
  esac
}
# $1: file description
# $2: loglevel
# $3: format string
# $4-: args
# level: quiet/panic/fatal/error/warning/info/verbose/debug/trace
printf_with_level() {
  [[ $# -ge 3 ]] || return 2
	local fd="$1"
	local loglevel="$2"
	local format_str="$3"
	shift 3

  local rank threshold
  rank=$(_log_rank "$loglevel") || return
  threshold=$(_log_rank "${LOG_LEVEL:-trace}") || return
  [[ $loglevel != quiet ]] || return 0
  # Fatal events retain their exit semantics even when output is suppressed.
  if [[ $rank -gt $threshold ]]; then
    if [[ $loglevel == fatal || $loglevel == panic ]]; then exit 1; fi
    return 0
  fi
	local control_code=''

	# pays tribute to FFmpeg's loglevel
	case "${loglevel}" in
	quiet)
		return 0
		;;
	panic)
		# text highlight, underline, text color is red, bg color is yellow
		control_code=${CONTROL_CODE_HIGHLIGHT}${CONTROL_CODE_SPERATOR}${TEXT_COLOR_RED}${CONTROL_CODE_SPERATOR}${BACKGROUND_COLOR_YELLOW}
		;;
	fatal)
		# text highlight, text color is red, add underline
		control_code=${CONTROL_CODE_HIGHLIGHT}${CONTROL_CODE_SPERATOR}${CONTROL_CODE_UNDERLINE}${CONTROL_CODE_SPERATOR}${TEXT_COLOR_RED}
		;;
	error)
		# text highlight, text color is red
		control_code=${CONTROL_CODE_HIGHLIGHT}${CONTROL_CODE_SPERATOR}${TEXT_COLOR_RED}
		;;
	warning)
		# text highlight, text color is yellow
		control_code=${CONTROL_CODE_HIGHLIGHT}${CONTROL_CODE_SPERATOR}${TEXT_COLOR_YELLOW}
		;;
	info)
		control_code=${TEXT_COLOR_GREEN}
		;;
	verbose)
		control_code=${TEXT_COLOR_WHITE}
		;;
	debug)
		control_code=${TEXT_COLOR_BLUE}
		;;
	trace)
		control_code=${TEXT_COLOR_PINK}
		;;
	*)
		printf2stderr "error" "invalid loglevel:%s\n" "${loglevel}"
		# printf_with_level /dev/stderr "error" "invalid loglevel:%s\n" "${loglevel}"
		return 0
		;;
	esac

	printf "${CONTROL_CODE_PREFIX}${control_code}${CONTROL_CODE_SUFFIX}${format_str}${CONTROL_CODE_PREFIX}${CONTROL_CODE_CLOSE}${CONTROL_CODE_SUFFIX}" "$@" >&"${fd}"

	if [[ ${loglevel} == "panic" ]] || [[ ${loglevel} == "fatal" ]]; then
		exit 1
	fi
}

# $1: loglevel
# $2: format string
# $2-: args
printf2stderr() {
	#printf_with_level /dev/stderr "$@"
	printf_with_level 2 "$@"
}

# $1: loglevel
# $2: format string
# $3-: args
printf2stdout() {
	#printf_with_level /dev/stdout "$@"
	printf_with_level 1 "$@"
}

is_mac() {
	test "$(uname -s)" == "Darwin"
}

is_linux() {
	test "$(uname -s)" == "Linux"
}

command_exist() {
	command -v "$1"
}

# $1: concurrent
# $2: command
# $3-: data array
batch() (
	# A subshell keeps jobs, variables and file descriptors out of the caller.
	if [[ $# -lt 2 || ! $1 =~ ^[1-9][0-9]*$ || -z $2 ]]; then
		printf 'batch: invalid concurrency or command\n' >&2
		return 2
	fi
	local limit=$1 result=0 status pid arg
	local pids=() command=()
	# Retain the legacy "command args" API without evaluating shell code.
	read -r -a command <<<"$2"
	[[ ${#command[@]} -gt 0 ]] || return 2
	shift 2
	for arg in "$@"; do
		"${command[@]}" "${arg}" &
		pids+=("$!")
		if [[ ${#pids[@]} -ge ${limit} ]]; then
			if wait "${pids[0]}"; then :; else
				status=$?
				[[ ${result} -ne 0 ]] || result=${status}
			fi
			pids=("${pids[@]:1}")
		fi
	done
	# Bash 3.2 treats an empty array expansion as unset under nounset.
	if [[ ${#pids[@]} -gt 0 ]]; then
		for pid in "${pids[@]}"; do
			if wait "${pid}"; then :; else
				status=$?
				[[ ${result} -ne 0 ]] || result=${status}
			fi
		done
	fi
	return "${result}"
)

# $1: if condition
# $2-: command if condition is true
do_if() {
	if eval "test $1"; then
		shift
		"$@"
	fi
}
