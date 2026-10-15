#!/usr/bin/env bash
# Argument parsing only: sourcing this file never installs or configures anything.

print_usage() {
  cat <<'USAGE'
Usage: ./build.sh [options]

  --help, -h                  Show this help without changing the system
  --only=APP,APP              Run only the selected applications
  --skip-system               Skip OS setup (requires prepared dependencies)
  --operator=OP               install (default), upgrade, uninstall, rollback
  --optional=true|false       Include optional applications
  --enable-APP                Add an application
  --disable-APP               Exclude an application
  --concurrent=N              Maximum concurrent tasks (default: 5)
  --timeout=SECONDS           Per-application timeout (default: 7200)
  --with-linux=docker|vm      Linux environment from macOS
  --linux_env_name=NAME       Linux environment name
  --linux_user=USER           Linux user name
  --linux_normal_passwd=VALUE Linux user password
  --linux_root_passwd=VALUE   Linux root password
  --app_flag=APP=VALUE        Application-specific value; repeatable
  --clean_cache               Remove the repository's success cache and exit

Installation requires Bash 4+. Help and argument validation work with Bash 3.2.
USAGE
}

_cli_error() {
  printf 'invalid argument: %s\n' "$1" >&2
  return 2
}

parse_cli() {
  OPTIONAL=false
  WITH_LINUX=false
  LINUX_ENV_NAME=linux-dev-env
  LINUX_USER=${USER:-$(whoami)}
  LINUX_NORMAL_PASSWD=''
  LINUX_ROOT_PASSWD=''
  OPERATOR=install
  ENABLE_APPS=()
  DISABLE_APPS=()
  APP_FLAG_ARGS=()
  ONLY_APPS=()
  SKIP_SYSTEM=false
  CONCURRENT=5
  TIMEOUT=7200
  SHOW_HELP=false
  CLEAN_CACHE=false

  local arg value app
  for arg in "$@"; do
    case "$arg" in
      --help|-h) SHOW_HELP=true ;;
      --skip-system) SKIP_SYSTEM=true ;;
      --only=*)
        value=${arg#*=}
        [[ "$value" =~ ^[[:alnum:]_][[:alnum:]_.+@*-]*(,[[:alnum:]_][[:alnum:]_.+@*-]*)*$ ]] || {
          _cli_error '--only expects comma-separated application names'; return 2;
        }
        IFS=, read -r -a ONLY_APPS <<<"$value" ;;

      --optional=*)
        case "${arg#*=}" in
          true|True|t|T|1) OPTIONAL=true ;;
          false|False|f|F|0) OPTIONAL=false ;;
          *) _cli_error '--optional expects true or false'; return 2 ;;
        esac ;;
      --with-linux=*)
        value=${arg#*=}
        case "$value" in
          vm|docker) WITH_LINUX=$value ;;
          *) _cli_error '--with-linux expects docker or vm'; return 2 ;;
        esac ;;
      --operator=*)
        value=${arg#*=}
        case "$value" in
          install|upgrade|uninstall|rollback) OPERATOR=$value ;;
          *) _cli_error '--operator expects install, upgrade, uninstall or rollback'; return 2 ;;
        esac ;;
      --concurrent=*|--timeout=*)
        value=${arg#*=}
        [[ "$value" =~ ^[1-9][0-9]*$ ]] || {
          _cli_error "${arg%%=*} expects a positive integer"; return 2;
        }
        if [[ "$arg" == --concurrent=* ]]; then CONCURRENT=$value; else TIMEOUT=$value; fi ;;
      --enable-*|--disable-*)
        app=${arg#--*-}
        [[ "$app" =~ ^[[:alnum:]_][[:alnum:]_.+@*-]*$ ]] || {
          _cli_error 'invalid application name'; return 2;
        }
        if [[ "$arg" == --enable-* ]]; then ENABLE_APPS+=("$app"); else DISABLE_APPS+=("$app"); fi ;;
      --app_flag=*)
        value=${arg#--app_flag=}
        app=${value%%=*}
        [[ "$value" == *=* && "$app" =~ ^[[:alnum:]_][[:alnum:]_.+@*-]*$ ]] || {
          _cli_error '--app_flag expects APP=VALUE'; return 2;
        }
        APP_FLAG_ARGS+=("$value") ;;
      --linux_env_name=*)
        LINUX_ENV_NAME=${arg#*=}
        [[ -n "$LINUX_ENV_NAME" ]] || { _cli_error 'empty Linux environment name'; return 2; } ;;
      --linux_user=*)
        LINUX_USER=${arg#*=}
        [[ -n "$LINUX_USER" ]] || { _cli_error 'empty Linux user'; return 2; } ;;
      --linux_normal_passwd=*) LINUX_NORMAL_PASSWD=${arg#*=} ;;
      --linux_root_passwd=*) LINUX_ROOT_PASSWD=${arg#*=} ;;
      --clean_cache) CLEAN_CACHE=true ;;
      *) _cli_error "unknown option ${arg%%=*}"; return 2 ;;
    esac
  done
}
