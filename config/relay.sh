#!/usr/bin/env bash

set -euo pipefail
[[ $# -gt 0 ]] || { printf 'usage: relay HOST [COMMAND ...]\n' >&2; exit 2; }
# OpenSSH owns Host aliases, User, IdentityFile and ProxyJump. No password is
# placed on a command line. Legacy expect login requires explicit opt-in.
if [[ ${DEV_ENV_LEGACY_LOGIN:-false} != true ]]; then
    host=$1
    shift
    if [[ ${1:-} == status ]]; then shift; set -- '/usr/local/bin/mutagen sync list' "$@"; fi
    exec ssh "$host" "$@"
fi

case $1 in
    mac)
        user=${HOST_USER}
        passwd=${HOST_PASSWD}
        mechine=host.docker.internal # or gateway.docker.internal
        relay="-"
        ;;
    *) #mechine of company
        user=${COMPANY_USER}
        passwd=${COMPANY_PASSWD}
        mechine=$1
        relay=${RELAY_ADDR}
        ;;
esac

shift

case ${1:-} in
    status)
        set -- "/usr/local/bin/mutagen sync list"
        ;;
    *)
        ;;
esac

"${HOME}"/.ssh/login "${mechine}" "${user}" "${passwd}" "${relay}" "$@"
