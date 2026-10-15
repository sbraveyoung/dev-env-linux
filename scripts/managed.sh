#!/usr/bin/env bash
REPO_ROOT=${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}
# These overrides share version resolution, private prefixes and safe link ownership.
source "$REPO_ROOT/scripts/catalog.sh"
declare -A MANAGED_INSTALL_APPS=()
managed_app() {
  APP_PATH="$APP_PATH" BIN_PATH="$BIN_PATH" python3 "${REPO_ROOT}/scripts/managed.py" "$1" "$2"
}
_managed_names=$(catalog_query managed) || return
for _managed in $_managed_names; do
  MANAGED_INSTALL_APPS[$_managed]=true
  eval "install_linux_${_managed}() { managed_app '${_managed}' install; }"
  eval "upgrade_linux_${_managed}() { managed_app '${_managed}' upgrade; }"
  eval "uninstall_linux_${_managed}() { managed_app '${_managed}' uninstall; }"
  eval "rollback_linux_${_managed}() { managed_app '${_managed}' rollback; }"
  eval "preinstall_linux_${_managed}() { managed_dependencies '${_managed}'; }"
  eval "preupgrade_linux_${_managed}() { managed_dependencies '${_managed}'; }"
done
unset _managed
# Platform-specific native preferences are declared per application.
_native_identity=$(. /etc/os-release; printf '%s' "$ID")
_native_rows=$(catalog_query native --distro "${DISTRO:-}" --distro-id "$_native_identity") || return
while IFS=$'\t' read -r _app _package; do
  [[ -n $_app ]] || continue
  unset "MANAGED_INSTALL_APPS[$_app]"
  eval "install_linux_${_app}() { pkg_install '${_package}'; }"
  eval "upgrade_linux_${_app}() { pkg_upgrade '${_package}'; }"
  eval "uninstall_linux_${_app}() { pkg_remove '${_package}'; }"
done <<< "$_native_rows"
unset _native_identity _native_rows _app _package _managed_names
install_linux_forgit() { printf 'forgit download is disabled in this configuration\n' >&2; return 2; }

# PathPicker is linked by the managed installer, so the old config hook must not
# redirect the command to an obsolete unversioned directory.
config_linux_PathPicker() { :; }

managed_dependencies() {
  local backend
  backend=$(catalog_field "$1" managed.backend) || return
  local -a CATALOG_DEPENDENCIES=()
  case "$backend" in npm|pip|source|git) catalog_load dependencies "$backend" --distro "$DISTRO" || return ;; esac
  case "$backend" in
    go) command -v go >/dev/null 2>&1 || install_linux_golang ;;
    cargo) command -v cargo >/dev/null 2>&1 || install_linux_rust ;;
    npm) command -v npm >/dev/null 2>&1 || pkg_install "${CATALOG_DEPENDENCIES[@]}" ;;
    pip) if ! python3 -c 'import ensurepip' >/dev/null 2>&1; then pkg_install "${CATALOG_DEPENDENCIES[@]}"; fi ;;
    source) pkg_install "${CATALOG_DEPENDENCIES[@]}" ;;
    git) command -v git >/dev/null 2>&1 || pkg_install "${CATALOG_DEPENDENCIES[@]}" ;;
  esac
}

# Debian binary names differ from upstream CLI names.
native_link() {
  local target link
  target=$(command -v "$1") || return
  link="$BIN_PATH/$2"
  if [[ ! -e "$link" && ! -L "$link" ]]; then ln -s "$target" "$link"; fi
}
config_linux_fd-find() { command -v fd >/dev/null 2>&1 || native_link fdfind fd; }
config_linux_bat() { command -v bat >/dev/null 2>&1 || native_link batcat bat; }

config_linux_exa() { command -v exa >/dev/null 2>&1 || native_link eza exa; }
if [[ ${DISTRO:-} == apt ]]; then
  uninstall_linux_fd-find() {
    pkg_remove "$(catalog_field fd-find native.apt)" || return
    [[ ! -L "$BIN_PATH/fd" || $(readlink "$BIN_PATH/fd") != /usr/bin/fdfind ]] || rm -- "$BIN_PATH/fd"
  }
  uninstall_linux_bat() {
    pkg_remove "$(catalog_field bat native.apt)" || return
    [[ ! -L "$BIN_PATH/bat" || $(readlink "$BIN_PATH/bat") != /usr/bin/batcat ]] || rm -- "$BIN_PATH/bat"
  }
  uninstall_linux_exa() {
    pkg_remove "$(catalog_field exa native.apt)" || return
    [[ ! -L "$BIN_PATH/exa" || $(readlink "$BIN_PATH/exa") != /usr/bin/eza ]] || rm -- "$BIN_PATH/exa"
  }
fi
