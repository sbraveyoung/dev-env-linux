#!/usr/bin/env bash

set -exuo pipefail

source common_defines.sh

if ! is_mac
then
    exit 1
fi

source setup_macos_apps.sh
source setup_macos_system.sh
