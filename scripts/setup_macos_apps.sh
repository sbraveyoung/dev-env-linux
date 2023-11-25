#!/usr/bin/env bash

set -exuo pipefail

########################## list of apps that to be install/upgrade/uninstall ###########################
# base software
brew_apps=(wechat raycast google-chrome obsidian dash alacritty ffmpeg@6)
customized_apps=(wetype)

# optional software
if [[ ${OPTIONAL} = true ]]; then # XXX: will wrong when use `if [[ ${OPTIONAL} ]]`
	brew_apps=("${brew_apps[@]}" orbstack alfred utools typora qqmusic arc snipaste telegram tencent-lemon tencent-meeting trojanx handbrake avidemux vlc audacity mediainfo obs zenmap xquartz figma)
	customized_apps=("${customized_apps[@]}" He3 YuvEye YUView StreamEye FlvParser H264Naked)
fi

# develop on a mac, and install necessary development tools
if [[ ${WITH_LINUX} = false ]]; then
	brew_apps=("${brew_apps[@]}" visual-studio-code gnu-sed gawk lrzsz coreutils jetbrains-toolbox ctags python3 cmake fzf cmake wget nvm icdiff fd the_silver_searcher nvim tmux git ssh-copy-id ranger cloc)
fi

# you can install custom software by providing install/upgrade/uninstall functions in the shell environment
if [[ ${#ENABLE_APPS[@]} -ne 0 ]]; then
	for app in "${ENABLE_APPS[@]}"; do
		customized_apps=("${customized_apps[@]}" "${app}")
	done
fi

# you can disable one or more software
if [[ ${#DISABLE_APPS[@]} -ne 0 ]]; then
	for app in "${DISABLE_APPS[@]}"; do
		for ((i = 0; i < ${#brew_apps[@]}; i++)); do
			if [[ ${brew_apps[i]} == "${app}" ]]; then
				unset "brew_apps[i]"
			fi
		done

		for ((i = 0; i < ${#customized_apps[@]}; i++)); do
			if [[ ${customized_apps[i]} == "${app}" ]]; then
				unset "customized_apps[i]"
			fi
		done
	done
fi
########################## list of apps that to be install/upgrade/uninstall ###########################

################################ app install/config/upgrade/uninstall functions ################################
for brew_app in "${brew_apps[@]}"; do
	eval "function install_darwin_${brew_app}(){
        # check if the app is installed by brew
        if brew list ${brew_app}
        then
            printf2stdout \"verbose\" \"the %s is is already installed by berw, continue...\\n\" ${brew_app}
            return 0
        fi

        set +e
        trap \"set -e\" RETURN
        output=\$(brew install ${brew_app} 2>&1)
        if [[ \$? -ne 0 ]]
        then
            if echo \${output} | grep \"It seems there is already an App at\"
            then
                printf2stdout \"verbose\" \"the %s is installed by other ways, continue...\\n\" ${brew_app}
                return 0
            else
                printf2stderr \"warning\" \"install %s with command 'brew install %s' failed.\n\" ${brew_app} ${brew_app}
                exit 1
            fi
        fi
    }"

	#eval "function config_darwin_${brew_app}(){
	#}"

	eval "function upgrade_darwin_${brew_app}(){
        # check if the app is installed by brew
        if brew list ${brew_app}
        then
            printf2stderr \"warning\" \"the app:%s was not installed or not installed by brew\n\" ${brew_app}
            return 0
        fi

        brew upgrade ${brew_app}
    }"

	eval "function uninstall_darwin_${brew_app}(){
        # check if the app is installed by brew
        if brew list ${brew_app}
        then
            printf2stderr \"warning\" \"the app:%s was not installed or not installed by brew\n\" ${brew_app}
            return 0
        fi

        brew uninstall ${brew_app}
    }"
done

config_darwin_google-chrome() {
	# set chrome as default browser, the chrome app must be in closing status
	open -a "Google Chrome" --args --make-default-browser

	# set Safari as default browser
	#open -a "Safari" --args --make-default-browser
}

config_darwin_visual-studio-code() {
	# TODO: see https://github.com/bestswifter/macbootstrap
	echo ""
}

config_darwin_fzf() {
	"$(brew --prefix)"/opt/fzf/install --all
}

install_darwin_wetype() {
	#TODO: if the app or zip file is exist, and check the checksum
	cd "$1"
	version="0.9.8_201"
	do_if "! -f ${CLONE_PATH}/WeTypeInstaller_${version}.zip" wget_nx https://wetype.wxqcloud.qq.com/app/mac/0.9.8/WeTypeInstaller_${version}.zip -O ${CLONE_PATH}/WeTypeInstaller_${version}.zip
	do_if "! -d WeTypeInstaller_${version}.app" unzip WeTypeInstaller_${version}.zip
	do_if "! -d /Applications/WeTypeInstaller_${version}.app" mv WeTypeInstaller_${version}.app /Applications
}

install_darwin_He3() {
	# TODO: implement
	return 0
}

install_darwin_YuvEye() {
	# TODO: implement
	return 0
}

install_darwin_YUView() {
	# TODO: implement
	return 0
}

install_darwin_StreamEye() {
	# TODO: implement
	return 0
}

install_darwin_FlvParser() {
	# TODO: implement
	return 0
}

install_darwin_H264Naked() {
	# TODO: implement
	return 0
}

config_darwin_orbstack() {
	if [[ ${WITH_LINUX} != false ]]; then
		source setup_linux_${WITH_LINUX}.sh
	fi
}

config_darwin_alacritty() {
	brew tap homebrew/cask-fonts
	brew install font-jetbrains-mono-nerd-font # or other fonts you like, see: https://www.nerdfonts.com/ or https://github.com/ryanoasis/nerd-fonts
	fc-cache -fv

	cat >>~/.config/alacritty/alacritty.yml <<EOF
font:
  normal:
    family: JetBrainsMono Nerd
    style: Regular
EOF
}

config_darwin_kitty() {
	# TODO: implement
	return 0
}
################################ app install/config/upgrade/uninstall functions ################################

tmp_dir=${CLONE_PATH}
trap "sudo rm -rf ${tmp_dir}" EXIT

# install homebrew
if ! command_exist brew; then
	/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

(batch_wrapper "${brew_apps[@]}")
(batch_wrapper "${customized_apps[@]}")
