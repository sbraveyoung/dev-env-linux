#!/usr/bin/env bash
# =============================================================================
# CentOS / RHEL / Fedora 发行版驱动
#
# 对外暴露统一接口：
#   pkg_install()          安装包
#   pkg_remove()           卸载包
#   pkg_update()           更新软件源并升级
#   pkg_group_install()    安装包组
#   pkg_system_setup()     系统初始化（repo 配置、首次 update 等）
#   DISTRO_PKG_APPS        基础系统包列表
#   DISTRO_OPTIONAL_PKG_APPS  可选系统包列表（--optional=true 时追加）
#
# 上层脚本（setup_linux_apps.sh / setup_linux_system.sh）只调用这些接口，
# 不包含任何 dnf/apt 硬编码，切换发行版只需替换驱动文件。
# =============================================================================

# -----------------------------------------------------------------------------
# 包管理接口
# -----------------------------------------------------------------------------

pkg_install()       { sudo dnf install -y "$@"; }
pkg_remove()        { sudo dnf remove  -y "$@"; }
pkg_update()        { sudo dnf clean all && sudo dnf update --assumeyes; }
pkg_group_install() { sudo dnf -y group install "$@"; }
pkg_upgrade() { sudo dnf upgrade -y "$@"; }
pkg_install_file() { pkg_install "$@"; }


# 系统初始化：配置必要的第三方 repo、安全策略并执行首次更新。
# 由 setup_linux_system.sh 通过 execute_if_not_success 调用，保证幂等。
pkg_system_setup() {
	local distro version
	distro=$(. /etc/os-release; printf '%s' "$ID")
	version=$(. /etc/os-release; printf '%s' "$VERSION_ID")
	pkg_install dnf-plugins-core
	case "$distro" in
		fedora)
			# Fedora does not have EPEL, CRB, yum-utils or RHEL %rhel.
			pkg_install "https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-${version}.noarch.rpm"
			;;
		centos|rhel|rocky|almalinux|ol)
			version=${version%%.*}
			pkg_install "https://dl.fedoraproject.org/pub/epel/epel-release-latest-${version}.noarch.rpm"
			if command -v dnf5 >/dev/null 2>&1; then
				sudo dnf config-manager enable crb
			else
				sudo dnf config-manager --set-enabled crb
			fi
			pkg_install "https://download1.rpmfusion.org/free/el/rpmfusion-free-release-${version}.noarch.rpm"
			;;
		*) printf 'unsupported DNF distribution: %s\n' "$distro" >&2; return 2 ;;
	esac
	pkg_update
}

# -----------------------------------------------------------------------------
# 发行版特有的钩子函数
# （命名遵循 common_defines.sh 约定：preinstall/config_linux_<app>）
# -----------------------------------------------------------------------------

# x264 在较新的 RHEL/CentOS 上需要放宽加密策略才能安装
preinstall_linux_x264-devel() {
	# CentOS 9 或更早版本；CentOS 10 需要 crypto-policies-scripts，策略需另行选择。
	# sudo update-crypto-policies --set LEGACY
	# Installing multimedia packages must not downgrade the system crypto policy.
	:
}

# neovim 依赖 lazygit，RHEL 系通过 copr 仓库安装
config_linux_neovim() {
	# neovim works without a separate optional Git UI.
	:
}

# -----------------------------------------------------------------------------
# 基础系统包列表（每行一个语义分组，便于跨发行版对比和维护）
# -----------------------------------------------------------------------------

# 可选系统包（--optional=true 时由 setup_linux_apps.sh 合并进 DISTRO_PKG_APPS）


source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/catalog.sh"
catalog_load packages --distro dnf
