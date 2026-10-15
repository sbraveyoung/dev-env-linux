#!/usr/bin/env bash
# =============================================================================
# Ubuntu / Debian 发行版驱动
#
# 实现与 dnf.sh 完全相同的接口，保证上层代码对发行版零感知。
# 包名已按 Ubuntu/Debian 命名规范映射（部分与 RHEL 不同）。
# =============================================================================

# -----------------------------------------------------------------------------
# 包管理接口
# -----------------------------------------------------------------------------

pkg_install()       { sudo env DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=120 install -y --no-install-recommends "$@"; }
pkg_remove()        { sudo env DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=120 remove -y "$@"; }
pkg_update()        { sudo apt-get update && sudo env DEBIAN_FRONTEND=noninteractive apt-get upgrade -y; }

# APT 没有"组"的概念；build-essential 已放入 DISTRO_PKG_APPS，此处透传即可
pkg_group_install() { pkg_install "$@"; }
pkg_upgrade() { pkg_install --only-upgrade "$@"; }
pkg_install_file() { pkg_install "$@"; }


# 系统初始化：添加必要的第三方源（GitHub CLI 等）并执行首次更新
pkg_system_setup() {
	sudo apt-get update
	pkg_install ca-certificates curl

	# GitHub CLI
	curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
		| sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
	sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
	echo "deb [arch=$(dpkg --print-architecture) \
		signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
		https://cli.github.com/packages stable main" \
		| sudo tee /etc/apt/sources.list.d/github-cli.list

	pkg_update
}

# -----------------------------------------------------------------------------
# 发行版特有的钩子函数
# -----------------------------------------------------------------------------

# x264 在 Ubuntu 上无需特殊加密策略，此钩子为空（保持接口对称）
preinstall_linux_x264-devel() { :; }

# neovim 依赖 lazygit，Ubuntu 系通过 PPA 安装
config_linux_neovim() {
	# Do not add an Ubuntu PPA to Debian; lazygit is optional to neovim.
	:
}

# -----------------------------------------------------------------------------
# 基础系统包列表（与 dnf.sh 按语义分组对齐，便于维护和对比）
# -----------------------------------------------------------------------------

# 可选系统包（与 dnf.sh 对应，包名已按 Ubuntu 规范映射）

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/catalog.sh"
catalog_load packages --distro apt
