#!/usr/bin/env bash

set -euo pipefail

source common_defines.sh

if ! is_linux; then
	exit 1
fi

# =============================================================================
# 发行版探测：这是整个项目中唯一感知具体发行版的地方。
# 探测结果写入 DISTRO 变量，后续所有脚本通过加载对应驱动获得
# pkg_install / pkg_remove / pkg_system_setup / DISTRO_PKG_APPS 等标准接口，
# 不再需要在各处散落 if is_ubuntu / elif is_centos 的判断。
# =============================================================================
_detect_distro() {
	if command -v dnf &>/dev/null; then
		echo "dnf"
	elif command -v apt-get &>/dev/null; then
		echo "apt"
	else
		printf2stderr "fatal" \
			"不支持的 Linux 发行版：未找到 dnf 或 apt-get，请手动添加对应的 distro 驱动。\n"
	fi
}

export DISTRO
DISTRO=$(_detect_distro)
printf2stdout "info" "发行版驱动：%s（驱动文件：distro/%s.sh）\n" "${DISTRO}" "${DISTRO}"

# Python is the declaration reader; bootstrap it before loading JSON data.
if ! command -v python3 >/dev/null 2>&1; then
  case "$DISTRO" in
    apt) sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 ;;
    dnf) sudo dnf install -y python3 ;;
  esac
fi
# 加载发行版驱动，定义 pkg_* 接口函数和 DISTRO_PKG_APPS 等变量
source "$(dirname "${BASH_SOURCE[0]}")/distro/${DISTRO}.sh"

RUN_SYSTEM_SETUP=true
source setup_linux_apps.sh
