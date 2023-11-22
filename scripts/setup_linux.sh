#!/usr/bin/env bash

set -exuo pipefail

source common_defines.sh

if ! is_linux
then
    exit 1
fi

source setup_linux_system.sh
source setup_linux_apps.sh
