#!/usr/bin/env bash

set -euo pipefail

source common_defines.sh

if ! is_mac; then
	exit 1
fi

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/catalog.sh"
catalog_query validate

if [[ ${SKIP_SYSTEM:-false} != true && ${OPERATOR:-install} == install ]]; then
  source setup_macos_system.sh
fi
source setup_macos_apps.sh
