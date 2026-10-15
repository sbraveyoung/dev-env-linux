#!/usr/bin/env bash
# Declarations are JSON data; only the validated, shell-quoted renderer is evaluated.
_CATALOG_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
catalog_query() {
  python3 "$_CATALOG_ROOT/scripts/catalog.py" --config "${DEV_ENV_SOFTWARE_CATALOG:-$_CATALOG_ROOT/config/software.json}" "$@"
}
catalog_load() {
  local rendered
  rendered=$(catalog_query "$@") || return
  eval "$rendered"
}
catalog_field() { catalog_query field "$@"; }
