#!/bin/bash -x

case $1 in
    mac)
        user=${HOST_USER}
        passwd=${HOST_PASSWD}
        mechine=${HOST_IP}
        relay=""
        ;;
    *) #mechine of company
        user=${COMPANY_USER}
        passwd=${COMPANY_PASSWD}
        mechine=$1
        relay=${RELAY_ADDR}
        ;;
esac

${HOME}/.ssh/login ${mechine} ${user} ${passwd} ${relay}