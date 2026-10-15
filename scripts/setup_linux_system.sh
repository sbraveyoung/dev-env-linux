#!/usr/bin/env bash

set -euo pipefail

# 创建必要的工作目录
for directory in "${GOPATH}" "${CLONE_PATH}" "${APP_PATH}" "${BIN_PATH}"; do
  case "$directory" in
    "$HOME"/*)
      mkdir -p "$directory"
      # Repair directories created by earlier versions with sudo.
      if [[ ! -w "$directory" ]]; then
        sudo chown "$(id -u):$(id -g)" "$directory"
      fi
      ;;
    *) sudo mkdir -p "$directory" ;;
  esac
done
mkdir -p ~/.ssh
chmod 700 ~/.ssh

execute_if_not_success pkg_system_setup
if ! command -v ssh-keygen >/dev/null; then
  pkg_install "${DISTRO_SSH_CLIENT}"
fi

if [[ ! -e ~/.ssh/id_rsa ]]; then
	ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
fi

# 系统初始化（repo 配置、安全策略、首次 update 等）由发行版驱动负责实现。
# 此处只调用标准接口 pkg_system_setup()，不含任何 dnf/apt 硬编码。
# 若需要支持新发行版，只需在 distro/ 下新增对应驱动文件，此处无需改动。
sudo ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
