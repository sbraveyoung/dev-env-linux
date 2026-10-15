#!/usr/bin/env bash
_sheath_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$_sheath_dir/functions.sh"
source "$_sheath_dir/environments.sh"
# Interactive aliases must not shadow commands in noninteractive installers.
if [[ $- == *i* ]]; then
  source "$_sheath_dir/alias.sh"
  source "$_sheath_dir/configuration.sh"
fi
unset _sheath_dir
