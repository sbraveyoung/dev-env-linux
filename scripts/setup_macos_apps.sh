#!/usr/bin/env bash

set -euo pipefail
declare -p ONLY_APPS >/dev/null 2>&1 || ONLY_APPS=()
OPERATOR=${OPERATOR:-install}

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/catalog.sh"
_catalog_development=false
[[ $WITH_LINUX != false ]] || _catalog_development=true
catalog_load macos --optional "$OPTIONAL" --development "$_catalog_development"
unset _catalog_development

# you can install custom software by providing install/upgrade/uninstall functions in the shell environment
if [[ ${#ENABLE_APPS[@]} -ne 0 ]]; then
  for app in "${ENABLE_APPS[@]}"; do
    customized_apps=("${customized_apps[@]}" "${app}")
  done
fi

# you can disable one or more software
if [[ ${#DISABLE_APPS[@]} -ne 0 ]]; then
  for app in "${DISABLE_APPS[@]}"; do
    for i in "${!brew_apps[@]}"; do
      if [[ ${brew_apps[i]} == "${app}" ]]; then
        unset "brew_apps[i]"
      fi
    done

    for i in "${!customized_apps[@]}"; do
      if [[ ${customized_apps[i]} == "${app}" ]]; then
        unset "customized_apps[i]"
      fi
    done
  done
fi
########################## list of apps that to be install/upgrade/uninstall ###########################

################################ app install/config/upgrade/uninstall functions ################################
# Generate every declared brew hook, including tools selected with --only/--enable.
_brew_rows=$(catalog_query brew) || return
while IFS=$'\t' read -r brew_app brew_package brew_tap; do
  [[ -n $brew_app ]] || continue
  eval "function install_darwin_${brew_app}(){
        # check if the app is installed by brew
        if brew list '${brew_package}'
        then
            printf2stdout \"verbose\" \"the %s is is already installed by berw, continue...\\n\" ${brew_app}
            return 0
        fi

        [[ -z '${brew_tap}' ]] || brew tap '${brew_tap}' || return
        local output status
        if output=\$(brew install '${brew_package}' 2>&1); then
            return 0
        else
            status=\$?
        fi
        if [[ \$output == *'It seems there is already an App at'* ]]; then
            printf2stdout \"verbose\" \"the %s is installed by other ways, continue...\\n\" ${brew_app}
            return 0
        fi
        printf2stderr \"warning\" \"install %s with command 'brew install %s' failed.\n\" ${brew_app} ${brew_app}
        printf '%s\\n' \"\$output\" >&2
        return \"\$status\"
    }"

  #eval "function config_darwin_${brew_app}(){
  #}"

  eval "function upgrade_darwin_${brew_app}(){
        # Bug 修复：原逻辑 'if brew list' 在应用已安装时返回 0（真），导致进入分支后
        # 打印 warning 并 return，永远不会执行 brew upgrade。
        # 应为 'if ! brew list'：未安装才警告并跳过，已安装则继续升级。
        if ! brew list '${brew_package}' &>/dev/null
        then
            printf2stderr \"warning\" \"the app:%s was not installed or not installed by brew\n\" ${brew_app}
            return 0
        fi

        brew upgrade '${brew_package}'
    }"

  eval "function uninstall_darwin_${brew_app}(){
        # 同上：'if brew list' 判断反了，导致已安装的应用反而被 return 跳过。
        # 修复为 'if ! brew list'：未安装才警告并跳过，已安装则继续卸载。
        if ! brew list '${brew_package}' &>/dev/null
        then
            printf2stderr \"warning\" \"the app:%s was not installed or not installed by brew\n\" ${brew_app}
            return 0
        fi

        brew uninstall '${brew_package}'
    }"
done <<< "$_brew_rows"
unset _brew_rows brew_app brew_package brew_tap

_qt_names=$(catalog_query qt) || return
declare -A MANAGED_INSTALL_APPS=()
macos_qt_app() { python3 "${_CATALOG_ROOT}/scripts/macos_bundle.py" "$@"; }
for _qt_app in $_qt_names; do
  MANAGED_INSTALL_APPS[$_qt_app]=true
  for _qt_operation in install upgrade uninstall rollback; do
    eval "${_qt_operation}_darwin_${_qt_app}() { macos_qt_app '${_qt_app}' '${_qt_operation}'; }"
  done
done
unset _qt_names _qt_app _qt_operation

config_darwin_google-chrome() {
  # set chrome as default browser, the chrome app must be in closing status
  open -a "Google Chrome" --args --make-default-browser

  # set Safari as default browser
  #open -a "Safari" --args --make-default-browser
}

config_darwin_visual-studio-code() {
  python3 "${_CATALOG_ROOT}/scripts/macos_config.py" vscode
}

config_darwin_fzf() {
  "$(brew --prefix)"/opt/fzf/install --all
}

install_darwin_wetype() {
  local version archive bundle url
  cd "$1"
  version=$WETYPE_VERSION
  archive=$(catalog_field wetype darwin.archive --version "$version") || return
  bundle=$(catalog_field wetype darwin.bundle --version "$version") || return
  url=$(catalog_field wetype darwin.download_url --version "$version") || return
  do_if "! -f ${CLONE_PATH}/$archive" wget_nx "$url" -O "${CLONE_PATH}/$archive"
  do_if "! -d $bundle" unzip "$archive"
  do_if "! -d /Applications/$bundle" mv "$bundle" /Applications
}

# These sources require user/vendor information, so never report false success.
install_darwin_YuvEye() {
  printf 'YuvEye requires its official project/download URL; see TODO_STATUS.md\n' >&2
  return 2
}

install_darwin_StreamEye() {
  printf 'StreamEye requires a vendor-provided macOS installer and license; see TODO_STATUS.md\n' >&2
  return 2
}

config_darwin_orbstack() {
  if [[ ${WITH_LINUX} != false ]]; then
    source setup_linux_"${WITH_LINUX}".sh
  fi
}

config_darwin_alacritty() {
  brew tap "$(catalog_field alacritty darwin.font_tap)"
  brew install "$(catalog_field alacritty darwin.font_package)" # or other fonts you like, see: https://www.nerdfonts.com/ or https://github.com/ryanoasis/nerd-fonts
  fc-cache -fv

  mkdir -p ~/.config/alacritty
  cat >~/.config/alacritty/alacritty.yml <<EOF
font:
  normal:
    family: $(catalog_field alacritty darwin.font_family)
    style: Regular
EOF
}

config_darwin_kitty() {
  python3 "${_CATALOG_ROOT}/scripts/macos_config.py" kitty
}
################################ app install/config/upgrade/uninstall functions ################################

if [[ ${#ONLY_APPS[@]} -gt 0 ]]; then
  brew_apps=()
  customized_apps=()
  for app in "${ONLY_APPS[@]}"; do
    if command_exist "${OPERATOR}_darwin_${app}" >/dev/null; then
      customized_apps+=("$app")
    else
      printf 'unsupported %s operation for application: %s\n' "$OPERATOR" "$app" >&2
      return 2
    fi
  done
fi

tmp_dir=${CLONE_PATH}
# Sources may be shared or referenced by installed symlinks; retain them.

# install homebrew
if ! command_exist brew; then
  /bin/bash -c "$(curl -fsSL "$(catalog_query bootstrap homebrew)")"
fi

(batch_wrapper "${brew_apps[@]}")
(batch_wrapper "${customized_apps[@]}")
