#!/usr/bin/env bash

set -exuo pipefail

# XXX: orb linux vm does not support customize user name?
LINUX_USER=$(whoami)

if ! orbctl info ${LINUX_ENV_NAME}
then
    orbctl create centos ${LINUX_ENV_NAME}
fi
if [[ ${LINUX_NORMAL_PASSWD} != "" ]]
then
    orb -m ${LINUX_ENV_NAME} sudo passwd ${LINUX_USER} ${LINUX_NORMAL_PASSWD}
fi
if [[ ${LINUX_ROOT_PASSWD} != "" ]]
then
    #TODO
    echo ""
fi

cd ..

# TODO
orb -m ${LINUX_ENV_NAME} -u ${LINUX_USER} ./build.sh --optional=${OPTIONAL} --operator=${OPERATOR} --concurrent=${CONCURRENT} --timeout=${TIMEOUT} #--app_flags= --enable="${ENABLE_APPS[@]}" --disable-*
