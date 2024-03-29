#!/bin/bash

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

case $1 in
    status)
        set -- "/usr/local/bin/mutagen sync list"
        ;;
    *)
        ;;
esac

${HOME}/.ssh/login ${mechine} ${user} ${passwd} ${relay} $@
