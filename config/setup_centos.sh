#!/usr/bin/env bash
# Compatibility entry point: use the maintained distro driver and shared hooks.
set -euo pipefail
[[ $(uname -s) == Linux ]] || { echo "Run this entry point inside an isolated Linux environment" >&2; exit 2; }
command -v dnf >/dev/null 2>&1 || { echo "This compatibility entry point requires DNF" >&2; exit 2; }
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
exec bash "$repo_root/build.sh" "$@"
