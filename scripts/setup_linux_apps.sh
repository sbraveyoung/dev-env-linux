#!/usr/bin/env bash

set -euo pipefail
declare -p ONLY_APPS >/dev/null 2>&1 || ONLY_APPS=()
declare -p DISTRO_NATIVE_APPS >/dev/null 2>&1 || DISTRO_NATIVE_APPS=()
declare -p DISTRO_NATIVE_PACKAGES >/dev/null 2>&1 || declare -A DISTRO_NATIVE_PACKAGES=()
OPERATOR=${OPERATOR:-install}
CONCURRENT=${CONCURRENT:-5}

# Software selection and versions come from the validated declaration source.
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/catalog.sh"
catalog_load defaults --platform linux

_github_latest_version() {
  local url=$1
  local headers=()
  [[ -z ${GITHUB_TOKEN:-} ]] || headers=(-H "Authorization: token ${GITHUB_TOKEN}")
  curl -fsSL --connect-timeout 5 --max-time 15 "${headers[@]}" "$url" 2>/dev/null |
    grep -m1 '"tag_name"' | sed -E 's/.*"v?([^"]+)".*/\1/'
}
_golang_latest_version() {
  curl -fsSL --connect-timeout 5 --max-time 15 "$1" 2>/dev/null |
    grep -oE '"version"[[:space:]]*:[[:space:]]*"go[^"]*"' |
    sed -n '1{s/.*"go\([^"]*\)".*/\1/;p;}'
}
_resolve_latest_versions() {
  [[ ${SKIP_VERSION_CHECK:-true} != true ]] || return 0
  command_exist curl || return 0
  local variable provider url release
  while IFS=$'\t' read -r variable provider url; do
    case "$provider" in
      go) release=$(_golang_latest_version "$url") || release='' ;;
      github) release=$(_github_latest_version "$url") || release='' ;;
      *) return 2 ;;
    esac
    if [[ $release =~ ^[0-9]+([.][0-9]+)+(-[0-9]+)?$ ]]; then printf -v "$variable" '%s' "$release"; fi
  done < <(catalog_query latest)
  return 0
}

# 共享后端依赖由 managed.sh 的 managed_dependencies 按需安装。
########################## list of apps that to be install/upgrade/uninstall ###########################
# DISTRO_PKG_APPS / DISTRO_OPTIONAL_PKG_APPS 由发行版驱动（distro/${DISTRO}.sh）定义，
# 此处只做应用列表的合并与过滤，不感知任何具体的包管理器或包名。

# forgit 下载保持停用，因此不加入默认队列；显式选择时报告原因。
# 通过源码/脚本安装的自定义工具（与发行版无关）
catalog_load profile linux-default --shell-var customized_apps

# 可选包：系统包从驱动的 DISTRO_OPTIONAL_PKG_APPS 追加，自定义工具在此追加
if [[ ${OPTIONAL} = true ]]; then
	DISTRO_PKG_APPS=("${DISTRO_PKG_APPS[@]}" "${DISTRO_OPTIONAL_PKG_APPS[@]}")
	# 手动工具在 catalog 的 linux-manual 分组声明；此选项只追加系统依赖。
fi

# 通过 --enable-xxx 追加自定义应用
if [[ ${#ENABLE_APPS[@]} -ne 0 ]]; then
	for app in "${ENABLE_APPS[@]}"; do
		customized_apps=("${customized_apps[@]}" "${app}")
	done
fi

# 通过 --disable-xxx 从系统包和自定义包两个列表中同时移除
if [[ ${#DISABLE_APPS[@]} -ne 0 ]]; then
	for app in ${DISABLE_APPS[@]+"${DISABLE_APPS[@]}"}; do
		# unset 会留下稀疏索引；遍历实际索引，避免连续禁用时触发 set -u。
		for i in "${!DISTRO_PKG_APPS[@]}"; do
			if [[ ${DISTRO_PKG_APPS[i]} == "${app}" ]]; then
				unset "DISTRO_PKG_APPS[i]"
			fi
		done
		for i in "${!customized_apps[@]}"; do
			if [[ ${customized_apps[i]} == "${app}" ]]; then
				unset "customized_apps[i]"
			fi
		done
	done
fi
################################ app install/config/upgrade/uninstall functions ################################
# 根据 DISTRO_PKG_APPS 批量生成安装/卸载函数。
# 函数体调用 pkg_install / pkg_remove 抽象接口，不直接依赖 dnf 或 apt-get。
# 发行版切换时只需替换 distro/ 下的驱动文件，此处代码无需任何改动。
for _pkg in "${DISTRO_PKG_APPS[@]}" ${DISTRO_OPTIONAL_PKG_APPS[@]+"${DISTRO_OPTIONAL_PKG_APPS[@]}"}; do
	eval "install_linux_${_pkg}()   { pkg_install '${_pkg}'; }"
	eval "uninstall_linux_${_pkg}() { pkg_remove '${_pkg}'; }"
	eval "upgrade_linux_${_pkg}() { pkg_upgrade '${_pkg}'; }"
done
unset _pkg


config_linux_python3() {
	[[ -e "$BIN_PATH/python" ]] || ln -s "$(command -v python3)" "$BIN_PATH/python"
}

config_linux_python3-pip() {
	[[ -e "$BIN_PATH/pip" ]] || ln -s "$(command -v pip3)" "$BIN_PATH/pip"
}

install_linux_grv() {
	[[ $(linux_arch) == amd64 ]] || { printf 'grv has no configured ARM64 binary\n' >&2; return 2; }
	cd "${CLONE_PATH}"
	# GRV_VERSION 由声明默认值或环境覆盖提供。
	wget_nx "$(catalog_field grv download_url --version "$GRV_VERSION")" -O grv
	chmod +x grv
	cp grv "${APP_PATH}/grv"
}

install_linux_htop() {
	git_clone_nx "$(catalog_field htop source_url)" "${CLONE_PATH}"/htop
	cd "${CLONE_PATH}"/htop
	./autogen.sh
	./configure --prefix="${APP_PATH}"/htop
	make -j "$(nproc)"
	make install
	ln -sf "${APP_PATH}"/htop/bin/htop "${BIN_PATH}"/htop
}

# Bug 修复：原函数名 conifig_linux_PathPicker 存在拼写错误（conifig → config），
# common_defines.sh 中调用的是 config_$1_$3，因此该函数从未被执行过。

config_linux_tmux() {
	# tpm, tmux plugins manager
	git_clone_nx "$(catalog_field tmux plugin_url)" ~/.tmux/plugins/tpm
	# && tmux source ~/.tmux.conf
}

install_linux_sdl() {
	git_clone_nx "$(catalog_field sdl source_url)" "${CLONE_PATH}"/sdl
	cd "${CLONE_PATH}"/sdl
	cmake -S . -B build && cmake --build build && sudo cmake --install build
}

# 手动选择的 Vim 使用发行版包管理接口。
install_linux_vim() { pkg_install vim; }
upgrade_linux_vim() { pkg_upgrade vim; }
uninstall_linux_vim() { pkg_remove vim; }


install_linux_percol() {
	sudo pip2 install "$(catalog_field percol legacy_python_package)"
}
install_linux_flvlib() {
	sudo pip2 install "$(catalog_field flvlib legacy_python_package)"
}

preinstall_linux_iredis() {
	pkg_install pipx
}

golang_owned_sdk_link() {
	[[ -L "$APP_PATH/go" ]] || return 1
	local destination version
	destination=$(readlink "$APP_PATH/go") || return
	version=${destination#"$APP_PATH/golang-"}; version=${version%/go}
	[[ $version =~ ^[[:alnum:].+-]+$ && $destination == "$APP_PATH/golang-$version/go" ]]
}

install_linux_golang() {
	local arch archive target previous binary
	# Refuse foreign commands and SDK links before download, migration or activation.
	for binary in go gofmt; do
		if [[ -e "$BIN_PATH/$binary" || -L "$BIN_PATH/$binary" ]] &&
		  { [[ ! -L "$BIN_PATH/$binary" ]] || [[ $(readlink "$BIN_PATH/$binary") != "$APP_PATH/go/bin/$binary" ]]; }; then
			printf 'refusing unmanaged command: %s\n' "$BIN_PATH/$binary" >&2
			return 2
		fi
	done
	if [[ -L "$APP_PATH/go" ]] && ! golang_owned_sdk_link; then
		printf 'refusing unmanaged SDK link: %s\n' "$APP_PATH/go" >&2
		return 2
	fi
	arch=$(linux_arch) || return
	archive="${CLONE_PATH}/go${GOLANG_VERSION}.linux-${arch}.tar.gz"
	target="${APP_PATH}/golang-${GOLANG_VERSION}"
	# Reuse an old unversioned archive only if its embedded version matches.
	if [[ ! -s "$archive" && -s "${CLONE_PATH}/go.tar.gz" ]] &&
	  tar -xzOf "${CLONE_PATH}/go.tar.gz" go/VERSION | grep -qx "go${GOLANG_VERSION}"; then
		mv "${CLONE_PATH}/go.tar.gz" "$archive"
	fi
	if [[ ! -x "$target/go/bin/go" ]]; then
		wget_nx "$(catalog_field golang download_url --version "$GOLANG_VERSION" --arch "$arch")" -O "$archive"
		python3 "${REPO_ROOT}/scripts/verified_download.py" go "$archive" "$GOLANG_VERSION" "$arch"
		mkdir -p "$target"
		tar -xzf "$archive" -C "$target"
	fi
	if [[ -d "${APP_PATH}/go" && ! -L "${APP_PATH}/go" ]]; then
		previous="${APP_PATH}/go.previous.$(date +%s)"
		mv "${APP_PATH}/go" "$previous"
	fi
	ln -sfn "$target/go" "${APP_PATH}/go"
	ln -sf "${APP_PATH}/go/bin/go" "${BIN_PATH}/go"
	ln -sf "${APP_PATH}/go/bin/gofmt" "${BIN_PATH}/gofmt"
}

install_linux_aminal() {
	go install "$(catalog_field aminal module)"
}

install_linux_this-repo() {
  APP_PATH="$APP_PATH" python3 "$REPO_ROOT/scripts/dotfiles.py" install
}
upgrade_linux_this-repo() {
  APP_PATH="$APP_PATH" python3 "$REPO_ROOT/scripts/dotfiles.py" upgrade
}
uninstall_linux_this-repo() {
  APP_PATH="$APP_PATH" python3 "$REPO_ROOT/scripts/dotfiles.py" uninstall
}

install_linux_pomo() {
	git_clone_nx "$(catalog_field pomo source_url)" "${CLONE_PATH}"/pomo
	cd "${CLONE_PATH}"/pomo
	make
}

upgrade_linux_golang() { install_linux_golang; }
uninstall_linux_golang() {
  local binary
  if ! golang_owned_sdk_link; then
    printf 'no managed Go SDK link; preserved command entries\n'
    return 0
  fi
  for binary in go gofmt; do
    if [[ -L "$BIN_PATH/$binary" && $(readlink "$BIN_PATH/$binary") == "$APP_PATH/go/bin/$binary" ]]; then
      rm -- "$BIN_PATH/$binary"
    fi
  done
  if golang_owned_sdk_link; then rm -- "$APP_PATH/go"; fi
  return 0
}


################################ app install/config/upgrade/uninstall functions ################################
#sudo dnf -y remove mesa-libGL mesa-libGL-devel


source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/rust_sdk.sh"
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/managed.sh"


if [[ ${#ONLY_APPS[@]} -gt 0 ]]; then
  DISTRO_PKG_APPS=()
  customized_apps=("${ONLY_APPS[@]}")
fi
for app in "${customized_apps[@]}"; do
  for disabled in ${DISABLE_APPS[@]+"${DISABLE_APPS[@]}"}; do
    if [[ $app == "$disabled" ]]; then continue 2; fi
  done
  command_exist "${OPERATOR}_linux_${app}" >/dev/null || {
    printf 'unsupported %s operation for application: %s\n' "$OPERATOR" "$app" >&2
    return 2
  }
done
# --only also respects explicit exclusions.
for i in "${!customized_apps[@]}"; do
  for disabled in ${DISABLE_APPS[@]+"${DISABLE_APPS[@]}"}; do
    [[ ${customized_apps[i]} != "$disabled" ]] || unset 'customized_apps[i]'
  done
done

tmp_dir=${CLONE_PATH}
# Sources may be shared or referenced by installed symlinks; retain them.

# 对支持追踪的 SDK/自定义二进制使用声明中的版本查询来源。
for app in "${customized_apps[@]}"; do
  case "$app" in
    golang|grv) _resolve_latest_versions; break ;;
  esac
done

# Cached Go installation must not hide a changed requested version or architecture.
for app in "${customized_apps[@]}"; do
  if [[ $app == golang && ${OPERATOR:-install} == install && -n ${APP_PATH:-} && -n ${CACHE_FILE:-} ]]; then
    if [[ ! -x "${APP_PATH}/go/bin/go" ]] ||
      [[ $("${APP_PATH}/go/bin/go" version) != "go version go${GOLANG_VERSION} linux/$(linux_arch)" ]]; then
      invalidate_app_cache linux "$CLONE_PATH" golang
    fi
  fi
done

if [[ ${OPERATOR:-install} == install && -n ${CACHE_FILE:-} && -n ${APP_PATH:-} ]]; then
  for app in "${customized_apps[@]}"; do
    if [[ $app == rust ]] && { [[ ! -x "$APP_PATH/rust-sdk/cargo/bin/rustc" ]] ||
      [[ $(rust_sdk_command rustc --version) != "rustc ${RUST_VERSION} "* ]]; }; then
      invalidate_app_cache linux "$CLONE_PATH" "$app"
    fi
    if [[ $app == this-repo && ! -f "$APP_PATH/dotfiles/current.json" ]]; then
      invalidate_app_cache linux "$CLONE_PATH" "$app"
    fi
    if [[ $(declare -f "install_linux_${app}") == *managed_app* && $(python3 -c 'import json,sys; from pathlib import Path; p=Path(sys.argv[1]); print("yes" if p.exists() and json.loads(p.read_text()).get("schema",0)>=4 else "no")' "$APP_PATH/managed/$app/current.json") == no ]]; then
      invalidate_app_cache linux "$CLONE_PATH" "$app"
    fi
  done
fi

if [[ ${RUN_SYSTEM_SETUP:-false} == true && ${SKIP_SYSTEM:-false} != true && ${OPERATOR:-install} == install ]]; then
  source "${REPO_ROOT}/scripts/setup_linux_system.sh"
fi

# Package transactions must not run concurrently against the same database.
_saved_concurrent=$CONCURRENT
CONCURRENT=1
(batch_wrapper "${DISTRO_PKG_APPS[@]}")
(batch_wrapper "${customized_apps[@]}")
CONCURRENT=$_saved_concurrent
