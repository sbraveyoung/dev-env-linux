#!/usr/bin/env bash

set -exuo pipefail

NORMAL_USER=$(whoami)

HOME=/home/$NORMAL_USER
GOPATH=/home/$NORMAL_USER/code

# make necessary file and directories
sudo mkdir -p ${GOPATH} ${CLONE_PATH} ${APP_PATH} ${BIN_PATH}
sudo chmod a+w ${CLONE_PATH} ${APP_PATH} ${BIN_PATH}

if [[ ! -e ~/.ssh/id_rsa ]]
then
    ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
fi

# dnf configuration
#execute_if_not_success sudo dnf config-manager --set-enabled powertools
execute_if_not_success sudo dnf -y install dnf-plugins-core
execute_if_not_success sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
execute_if_not_success sudo dnf localinstall -y https://download1.rpmfusion.org/free/el/rpmfusion-free-release-7.noarch.rpm
execute_if_not_success sudo dnf -y install yum-utils
execute_if_not_success sudo dnf -y install epel-release
sudo dnf -y groupinstall 'Development Tools' #execute_if_not_success has a bug when the args contains any args which surrounding by ' or "
execute_if_not_success sudo dnf -y config-manager --set-enabled crb

sudo ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
