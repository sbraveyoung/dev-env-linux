#!/usr/bin/env bash

set -exuo pipefail

# make necessary file and directories
sudo mkdir -p ${GOPATH} ${CLONE_PATH} ${APP_PATH} ${BIN_PATH}
sudo chmod a+w ${CLONE_PATH} ${APP_PATH} ${BIN_PATH}

if [[ ! -e ~/.ssh/id_rsa ]]; then
	ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
fi

# dnf configuration
function linux_dnf_configuration() {
	#sudo dnf config-manager --set-enabled powertools
	sudo dnf -y install dnf-plugins-core
	sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
	sudo dnf localinstall -y https://download1.rpmfusion.org/free/el/rpmfusion-free-release-7.noarch.rpm
	sudo dnf -y install yum-utils
	sudo dnf -y install epel-release
	sudo dnf -y groupinstall 'Development Tools' #execute_if_not_success has a bug when the args contains any args which surrounding by ' or "
	sudo dnf -y config-manager --set-enabled crb
	sudo dnf clean all && sudo dnf update --assumeyes
}

execute_if_not_success linux_dnf_configuration
sudo ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
