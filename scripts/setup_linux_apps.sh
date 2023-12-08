#!/usr/bin/env bash

set -exuo pipefail

########################## list of apps that to be install/upgrade/uninstall ###########################
# base libraries
dnf_apps=(libgcc.i686 glibc-devel bison flex texinfo libtool zlib-devel bzip2-devel openssl-devel sqlite-devel readline-devel tk-devel xz-devel gettext pkg-config autoconf automake txt2man ncurses ncurses-devel tcl-devel net-tools llvm clang-libs clang-devel libX11-devel libXcursor-devel libXrandr-devel libXinerama-devel mesa-libGL-devel mesa-libGLU-devel freeglut-devel libXi-devel libevent libevent-devel asciidoc pcre-devel xz-devel bind-utils freetype-devel glib2-devel fontconfig-devel pango-devel privoxy initscripts cscope SDL2-devel mesa-dri-drivers coreutils protobuf-devel libwmf-devel ghostscript-devel gdbm-devel ninja-build)
# base tools
dnf_apps=("${dnf_apps[@]}" which sudo gcc gcc-c++ gdb git make unzip ctags expect passwd wget cmake figlet pkgconfig curl zsh)
# languages
dnf_apps=("${dnf_apps[@]}" perl nodejs python3 python3-pip python3-devel ruby lua luajit)
customized_apps=(axel bcal diff-so-fancy fff git-commander jq lsix PathPicker tig tmux neovim vifm yank insect shellcheck git-flow-completion git-quick-stats sdl ffmpeg mcfly mosh cloc svg-term-cli zx squoosh_cli bash-language-server setuptools httpie pybind11 iredis ranger-fm mdv thefuck mycli asciinema http-prompt yapf icdiff golang gron ccat dlv cheat fx fq yq lazydocker this-repo glances glow curlie duf dsq z rust fzf forgit lsd broot exa fd-find hexyl ripgrep sd bat procs gping bottom choose du-dust onefetch tealdeer pastel hyperfine git-delta xh zoxide fselect)

# optional app/libraries
if [[ ${OPTIONAL} = true ]]; then
	# usful libraries
	dnf_apps=("${dnf_apps[@]}" libpng libpng-devel libjpeg-devel x264-devel x264-libs libwebp-devel libde265 libheif* libtiff-devel ncdu nnn gh kakoune colordiff git-lfs the_silver_searcher ack fortune-mod tree)
	customized_apps=("${customized_apps[@]}" ImageMagick dive grv trash-cli FlameGraph)
fi

# you can install custom software by providing preinstall/install/upgrade/uninstall functions in the shell environment
if [[ ${#ENABLE_APPS[@]} -ne 0 ]]; then
	for app in "${ENABLE_APPS[@]}"; do
		customized_apps=("${customized_apps[@]}" "${app}")
	done
fi

# you can disable one or more software
if [[ ${#DISABLE_APPS[@]} -ne 0 ]]; then
	for app in "${DISABLE_APPS[@]}"; do
		for ((i = 0; i < ${#dnf_apps[@]}; i++)); do
			if [[ ${brew_apps[i]} == "${app}" ]]; then
				unset "dnf_apps[i]"
			fi
		done

		for ((i = 0; i < ${#customized_apps[@]}; i++)); do
			if [[ ${customized_apps[i]} == "${app}" ]]; then
				unset "customized_apps[i]"
			fi
		done
	done
fi
########################## other funny tools ##########################
#starship/manimlib/gor/mediainfo/ssh-chat/FlameGraph/ohmyzsh/ccache/prettyping/zellij
#gitflow/bash-it
#dnf install failed: python2 python2-pip python2-devel
#customized install failed: htop/github.com/liamg/aminal/pomo/percol/flvlib
#https://github.com/amix/vimrc.git
#https://github.com/github/hub.git
#https://github.com/flok99/multitail
#https://github.com/alebcay/awesome-shell
#https://github.com/lheric/GitlHEVCAnalyzer.git
#https://cht.sh/
#https://github.com/peco/peco
#https://github.com/ogham/dog.git
#https://github.com/p-e-w/hegemon.git
########################## other funny tools ##########################

########################## list of apps that to be install/upgrade/uninstall ###########################

################################ app install/config/upgrade/uninstall functions ################################
for dnf_app in "${dnf_apps[@]}"; do
	eval "function install_linux_${dnf_app}(){
        # check if the app is installed by dnf
        # TODO

        #set +e
        #trap \"set -e\" RETURN
        sudo dnf install -y ${dnf_app}
    }"

	eval "function uninstall_linux_${dnf_app}(){
        #set +e
        #trap \"set -e\" RETURN
        sudo dnf remove -y ${dnf_app}
    }"
done

preinstall_linux_x264-devel() {
	sudo update-crypto-policies --set DEFAULT:SHA1
}

config_linux_python3() {
	sudo ln -sf $(which python3) /usr/bin/python
}

config_linux_python3-pip() {
	sudo ln -sf $(which pip3) /usr/bin/pip
}

install_linux_ImageMagick() {
	git_clone_nx https://github.com/ImageMagick/ImageMagick ${CLONE_PATH}/ImageMagick
	cd ${CLONE_PATH}/ImageMagick
	git checkout 7.1.0-36
	./configure --prefix=${APP_PATH}/ImageMagick --with-heic=yes --with-jxl=yes --with-jpeg=yes --with-png=yes --with-webp=yes
	make -j $(nproc)
	make install

	ln -sf ${APP_PATH}/ImageMagick/bin/magick ${BIN_PATH}/magick
	ln -sf ${APP_PATH}/ImageMagick/bin/animate ${BIN_PATH}/animate
	ln -sf ${APP_PATH}/ImageMagick/bin/compare ${BIN_PATH}/compare
	ln -sf ${APP_PATH}/ImageMagick/bin/composite ${BIN_PATH}/composite
	ln -sf ${APP_PATH}/ImageMagick/bin/conjure ${BIN_PATH}/conjure
	ln -sf ${APP_PATH}/ImageMagick/bin/convert ${BIN_PATH}/convert
	ln -sf ${APP_PATH}/ImageMagick/bin/display ${BIN_PATH}/display
	ln -sf ${APP_PATH}/ImageMagick/bin/identify ${BIN_PATH}/identify
	ln -sf ${APP_PATH}/ImageMagick/bin/import ${BIN_PATH}/import
	ln -sf ${APP_PATH}/ImageMagick/bin/magick-script ${BIN_PATH}/magick-script
	ln -sf ${APP_PATH}/ImageMagick/bin/mogrify ${BIN_PATH}/mogrify
	ln -sf ${APP_PATH}/ImageMagick/bin/montage ${BIN_PATH}/montage
	ln -sf ${APP_PATH}/ImageMagick/bin/stream ${BIN_PATH}/stream
}

install_linux_dive() {
	cd ${CLONE_PATH}
	curl -OL https://github.com/wagoodman/dive/releases/download/v0.9.2/dive_0.9.2_linux_amd64.rpm
	sudo rpm -i dive_0.9.2_linux_amd64.rpm
}

install_linux_grv() {
	cd ${CLONE_PATH}
	wget_nx https://github.com/rgburke/grv/releases/download/v0.3.2/grv_v0.3.2_linux64 -O grv
	chmod +x grv
	cp grv ${APP_PATH}/grv
}

install_linux_axel() {
	cd ${CLONE_PATH}
	wget_nx https://github.com/axel-download-accelerator/axel/releases/download/v2.17.7/axel-2.17.7.tar.gz -O axel.tar.gz
	tar -zxvf axel.tar.gz
	cd axel-2.17.7
	cd ${CLONE_PATH}/axel-2.17.7
	./configure --prefix=${APP_PATH}/axel-2.17.7
	make -j $(nproc)
	make install
	ln -sf ${APP_PATH}/axel-2.17.7/bin/axel ${BIN_PATH}/axel
}

install_linux_bcal() {
	git_clone_nx https://github.com/jarun/bcal ${CLONE_PATH}/bcal
	cd ${CLONE_PATH}/bcal
	make -j $(nproc)
	make strip install PREFIX=${APP_PATH}/bcal
}

install_linux_diff-so-fancy() {
	git_clone_nx https://github.com/so-fancy/diff-so-fancy ${APP_PATH}/diff-so-fancy
	ln -sf ${APP_PATH}/diff-so-fancy/diff-so-fancy ${BIN_PATH}/diff-so-fancy
}

install_linux_fff() {
	git_clone_nx https://github.com/dylanaraps/fff ${CLONE_PATH}/fff
	cd ${CLONE_PATH}/fff
	make PREFIX=${APP_PATH}/fff install
	ln -sf ${APP_PATH}/fff/bin/fff ${BIN_PATH}/fff
}

install_linux_git-commander() {
	git_clone_nx https://github.com/golbin/git-commander ${CLONE_PATH}/git-commander
	cd ${CLONE_PATH}/git-commander
	sudo npm -g install blessed lodash git-commander
}

install_linux_htop() {
	git_clone_nx https://github.com/hishamhm/htop ${CLONE_PATH}/htop
	cd ${CLONE_PATH}/htop
	./autogen.sh
	./configure --prefix=${APP_PATH}/htop
	make -j $(nproc)
	make install
	ln -sf ${APP_PATH}/htop/bin/htop ${BIN_PATH}/htop
}

install_linux_jq() {
	git_clone_nx https://github.com/stedolan/jq ${CLONE_PATH}/jq
	cd ${CLONE_PATH}/jq
	git submodule update --init
	autoreconf -fi
	./configure --prefix=${APP_PATH}/jq --with-oniguruma=builtin
	make -j $(nproc)
	make check
	make install
	ln -sf ${APP_PATH}/jq/bin/jq ${BIN_PATH}/jq
}

install_linux_lsix() {
	git_clone_nx https://github.com/hackerb9/lsix ${APP_PATH}/lsix
	ln -sf ${APP_PATH}/lsix ${BIN_PATH}/lsix
}

install_linux_PathPicker() {
	git_clone_nx https://github.com/facebook/PathPicker ${APP_PATH}/PathPicker
}

conifig_linux_PathPicker() {
	ln -sf ${APP_PATH}/PathPicker/fpp ${BIN_PATH}/fpp
}

install_linux_tig() {
	git_clone_nx https://github.com/jonas/tig ${CLONE_PATH}/tig
	cd ${CLONE_PATH}/tig
	make prefix=${APP_PATH}/tig
	make install prefix=${APP_PATH}/tig
	ln -sf ${APP_PATH}/tig/bin/tig ${BIN_PATH}/tig
}

install_linux_tmux() {
	git_clone_nx https://github.com/tmux/tmux ${CLONE_PATH}/tmux
	cd ${CLONE_PATH}/tmux
	sh autogen.sh
	./configure --prefix=${APP_PATH}/tmux
	make -j $(nproc)
	make install
	ln -sf ${APP_PATH}/tmux/bin/tmux ${BIN_PATH}/tmux
}

config_linux_tmux() {
	# tpm, tmux plugins manager
	git_clone_nx https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
	# && tmux source ~/.tmux.conf
}

install_linux_trash-cli() {
	git_clone_nx https://github.com/andreafrancia/trash-cli ${CLONE_PATH}/trash-cli
	cd ${CLONE_PATH}/trash-cli
	sudo python setup.py install
}

install_linux_vifm() {
	git_clone_nx https://github.com/vifm/vifm ${CLONE_PATH}/vifm
	cd ${CLONE_PATH}/vifm
	./scripts/fix-timestamps
	./configure --prefix=${APP_PATH}/vifm
	make
	make install
	ln -sf ${APP_PATH}/vifm/bin/vifm ${BIN_PATH}/vifm
}

install_linux_yank() {
	git_clone_nx https://github.com/mptre/yank ${CLONE_PATH}/yank
	cd ${CLONE_PATH}/yank
	make install PREFIX=${APP_PATH}/yank
	ln -sf ${APP_PATH}/yank/bin/yank ${BIN_PATH}/yank
}

install_linux_insect() {
	wget_nx https://github.com/sharkdp/insect/releases/download/v5.3.0/insect-linux-x64 -O ${APP_PATH}/insect-linux-x64
	ln -sf ${APP_PATH}/insect-linux-x64 ${BIN_PATH}/insect
}

install_linux_shellcheck() {
	cd ${CLONE_PATH}
	wget_nx https://github.com/koalaman/shellcheck/releases/download/stable/shellcheck-stable.linux.x86_64.tar.xz -O shellcheck.tar.xz
	tar xf shellcheck.tar.xz
	ln -sf ${CLONE_PATH}/shellcheck-stable/shellcheck ${BIN_PATH}/shellcheck
}

install_linux_git-flow-completion() {
	git_clone_nx https://github.com/bobthecow/git-flow-completion.git ${APP_PATH}/git-flow-completion
}

install_linux_git-quick-stats() {
	git_clone_nx https://github.com/arzzen/git-quick-stats.git ${CLONE_PATH}/git-quick-stats
	cd ${CLONE_PATH}/git-quick-stats
	make install PREFIX=${APP_PATH}
	ln -sf ${APP_PATH}/git-quick-stats ${BIN_PATH}/git-quick-stats
}

install_linux_FlameGraph() {
	git_clone_nx https://github.com/brendangregg/FlameGraph.git ${APP_PATH}/FlameGraph
}

install_linux_sdl() {
	git_clone_nx https://github.com/libsdl-org/SDL.git ${CLONE_PATH}/sdl
	cd ${CLONE_PATH}/sdl
	cmake -S . -B build && cmake --build build && sudo cmake --install build
}

preinstall_linux_ffmpeg() {
	wget $(echo "https://pkgs.dyn.su/el9/base/x86_64/raven-release.el9.noarch.rpm" | sed "s/el9/el$(rpm -q --queryformat '%{RELEASE}' rpm | grep -oP 'el\K[0-9]+')/g")
	sudo rpm -ivh raven-release*.rpm && rm -rf raven-release*.rpm
	sudo dnf clean all && sudo dnf update --assumeyes
}

install_linux_ffmpeg() {
	git_clone_nx https://git.ffmpeg.org/ffmpeg.git ${CLONE_PATH}/ffmpeg
	cd ${CLONE_PATH}/ffmpeg
	PKG_CONFIG_PATH=${PKG_CONFIG_PATH:-}:${APP_PATH}/sdl/lib/pkgconfig ./configure --prefix=${APP_PATH}/ffmpeg --enable-gpl --enable-libx264 --disable-x86asm --extra-cflags=-I${APP_PATH}/sdl/include --extra-ldflags=-L${APP_PATH}/sdl/lib --enable-shared
	make -j $(nproc)
	make install
	ln -sf ${APP_PATH}/ffmpeg/bin/ffmpeg ${BIN_PATH}/ffmpeg
	ln -sf ${APP_PATH}/ffmpeg/bin/ffprobe ${BIN_PATH}/ffprobe
	ln -sf ${APP_PATH}/ffmpeg/bin/ffplay ${BIN_PATH}/ffplay
}

install_linux_neovim() {
	git_clone_nx https://github.com/neovim/neovim.git ${CLONE_PATH}/neovim
	cd ${CLONE_PATH}/neovim
	git checkout stable
	make CMAKE_BUILD_TYPE=RelWithDebInfo CMAKE_EXTRA_FLAGS="-DCMAKE_INSTALL_PREFIX=${APP_PATH}/neovim"
	make install
	ln -sf ${APP_PATH}/neovim/bin/nvim ${BIN_PATH}/nvim
}

config_linux_neovim() {
	# required by lazyvim

	# lazygit
	sudo dnf copr enable atim/lazygit -y
	sudo dnf install -y lazygit
}

# not used
install_linux_vim() {
	git_clone_nx https://github.com/vim/vim.git ${CLONE_PATH}/vim
	cd ${CLONE_PATH}/vim
	./configure --prefix=${APP_PATH}/vim --with-features=huge --enable-multibyte --enable-python3interp=yes --with-python3-config-dir=/usr/lib64/python3.6/config-3.6m-x86_64-linux-gnu --enable-gui=gtk2 --enable-cscope
	make -j $(nproc)
	make install
	sudo mbak /usr/bin/vim
	ln -sf ${APP_PATH}/vim/bin/vim ${BIN_PATH}/vim
	ln -sf ${APP_PATH}/vim/bin/vimdiff ${BIN_PATH}/vimdiff
	ln -sf ${APP_PATH}/vim/bin/xxd ${BIN_PATH}/xxd
	hash -r
}

# not used
config_linux_vim() {
	# install xvim
	git_clone_nx https://github.com/adwpc/xvim.git ${CLONE_PATH}/xvim
	cd ${CLONE_PATH}/xvim
	yes | ./install vimrc
}

install_linux_mcfly() {
	curl -LSfs https://raw.githubusercontent.com/cantino/mcfly/master/ci/install.sh | sh -s -- --git cantino/mcfly
}

install_linux_mosh() {
	git_clone_nx https://github.com/mobile-shell/mosh ${CLONE_PATH}/mosh
	cd ${CLONE_PATH}/mosh
	./autogen.sh
	./configure --prefix=${APP_PATH}/mosh
	make
	make install

	ln -sf ${APP_PATH}/mosh/bin/mosh ${BIN_PATH}/mosh
	ln -sf ${APP_PATH}/mosh/bin/mosh-client ${BIN_PATH}/mosh-client
	ln -sf ${APP_PATH}/mosh/bin/mosh-server ${BIN_PATH}/mosh-server
}

install_linux_fx() {
	#sudo npm install -g fx fx-completion
	go install github.com/antonmedv/fx@latest
}
install_linux_cloc() {
	sudo npm install -g cloc
}
install_linux_svg-term-cli() {
	sudo npm install -g svg-term-cli
}
install_linux_zx() {
	sudo npm install -g zx
}
install_linux_squoosh_cli() {
	sudo npm install -g @squoosh/cli
}
install_linux_bash-language-server() {
	sudo npm install -g bash-language-server
}

install_linux_setuptools() {
	sudo python -m pip install --upgrade setuptools pip
}
install_linux_percol() {
	sudo pip2 install percol
}
install_linux_flvlib() {
	sudo pip2 install flvlib
}

install_linux_httpie() {
	sudo pip3 install --upgrade httpie
}
install_linux_pybind11() {
	sudo pip3 install --upgrade pybind11
}
preinstall_linux_iredis() {
	sudo dnf remove -y python3-packaging
}
install_linux_iredis() {
	sudo pip3 install --upgrade iredis
}
install_linux_ranger-fm() {
	sudo pip3 install --upgrade ranger-fm
}
install_linux_mdv() {
	sudo pip3 install --upgrade mdv
}
install_linux_thefuck() {
	sudo pip3 install --upgrade thefuck
}
install_linux_mycli() {
	sudo pip3 install --upgrade mycli
}
install_linux_asciinema() {
	sudo pip3 install --upgrade asciinema
}
install_linux_http-prompt() {
	sudo pip3 install --upgrade http-prompt
}
install_linux_yapf() {
	sudo pip3 install --upgrade yapf
}
install_linux_icdiff() {
	sudo pip3 install --upgrade icdiff
}

install_linux_golang() {
	wget_nx https://go.dev/dl/go1.21.0.linux-amd64.tar.gz -O ${CLONE_PATH}/go.tar.gz
	tar -zxvf ${CLONE_PATH}/go.tar.gz -C ${APP_PATH}

	ln -sf ${APP_PATH}/go/bin/go ${BIN_PATH}/go
	ln -sf ${APP_PATH}/go/bin/gofmt ${BIN_PATH}/gofmt
}

install_linux_gron() {
	go install github.com/tomnomnom/gron@latest
}
install_linux_ccat() {
	go install github.com/jingweno/ccat@latest
}
install_linux_dlv() {
	go install github.com/go-delve/delve/cmd/dlv@latest
}
install_linux_cheat() {
	go install github.com/cheat/cheat/cmd/cheat@latest
}
install_linux_fq() {
	go install github.com/wader/fq@latest
}
install_linux_yq() {
	go install github.com/mikefarah/yq/v4@latest
}
install_linux_lazydocker() {
	go install github.com/jesseduffield/lazydocker@latest
}
install_linux_aminal() {
	go install github.com/liamg/aminal@latest
}

install_linux_this-repo() {
	# .bashrc
	cat >>~/.bashrc <<EOF
source (cd ../sheath && pwd)/constant.sh
source (cd ../sheath && pwd)/alias.sh
source (cd ../sheath && pwd)/environments.sh
source (cd ../sheath && pwd)/functions.sh
source (cd ../sheath && pwd)/configuration.sh
EOF

	# NOTE: .gitconfig, you need to manually update your git user and email after the installation is complete
	mbak ~/.gitconfig
	cp ${REPO_ROOT}/config/.gitconfig ~/.gitconfig

	# XXX: about ssh, TBD...(to be determine)
	# [[ ! -e ~/.ssh ]] && { mkdir -p ~/.ssh }
	smart_cp ${REPO_ROOT}/config/relay.sh ~/.ssh/relay.sh
	smart_cp ${REPO_ROOT}/config/login ~/.ssh/login
	smart_cp ${REPO_ROOT}/config/.ssh_config ~/.ssh/.ssh_config

	# nvim
	mbak ~/.config/nvim
	smart_cp -r ${REPO_ROOT}/config/nvim ~/.config/nvim

	# .tigrc
	mbak ~/.tigrc
	cp ${REPO_ROOT}/config/.tigrc ~/.tigrc

	# NOTE: .tmux.conf, you need to manually install tmux plugins with `prefix+I` after the installation is complete
	# XXX: install tmux plugins automatically
	cp ${REPO_ROOT}/config/.tmux.conf ~/.tmux.conf

	# NOTE: .vimrc is deprecated
}

install_linux_pomo() {
	git_clone_nx https://github.com/kevinschoon/pomo.git ${CLONE_PATH}/pomo
	cd ${CLONE_PATH}/pomo
	make
}

install_linux_glances() {
	curl -L https://bit.ly/glances | /bin/bash
}

install_linux_glow() {
	git_clone_nx https://github.com/charmbracelet/glow.git ${CLONE_PATH}/glow
	cd ${CLONE_PATH}/glow
	go build
}

install_linux_curlie() {
	git_clone_nx https://github.com/rs/curlie.git ${CLONE_PATH}/curlie
	cd ${CLONE_PATH}/curlie
	go install
}

install_linux_duf() {
	git_clone_nx https://github.com/muesli/duf.git ${CLONE_PATH}/duf
	cd ${CLONE_PATH}/duf
	go install
}

install_linux_dsq() {
	git_clone_nx https://github.com/multiprocessio/dsq ${CLONE_PATH}/dsq
	cd ${CLONE_PATH}/dsq
	go install .
}

install_linux_z() {
	git_clone_nx https://github.com/rupa/z.git ${APP_PATH}/z
}

install_linux_fzf() {
	git_clone_nx --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
	~/.fzf/install
}

install_linux_forgit() {
	#similar to https://github.com/bigH/git-fuzzy
	# forgit
	mkdir -p ${APP_PATH}/forgit
	cd ${APP_PATH}/forgit
	wget_nx git.io/forgit -O forgit
}

install_linux_rust() {
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs >${CLONE_PATH}/rustup-init.sh
	chmod +x ${CLONE_PATH}/rustup-init.sh
	${CLONE_PATH}/rustup-init.sh -y
}

install_linux_lsd() {
	~/.cargo/bin/cargo install --git https://github.com/Peltoche/lsd.git --branch master
}
install_linux_broot() {
	~/.cargo/bin/cargo install broot
}
install_linux_exa() {
	~/.cargo/bin/cargo install exa
}
install_linux_fd-find() {
	~/.cargo/bin/cargo install fd-find
}
install_linux_hexyl() {
	~/.cargo/bin/cargo install hexyl
}
install_linux_ripgrep() {
	~/.cargo/bin/cargo install ripgrep
}
install_linux_sd() {
	~/.cargo/bin/cargo install sd
}
install_linux_bat() {
	~/.cargo/bin/cargo install bat
}
install_linux_procs() {
	~/.cargo/bin/cargo install procs
}
install_linux_gping() {
	~/.cargo/bin/cargo install gping
}
install_linux_bottom() {
	~/.cargo/bin/cargo install bottom
}
install_linux_choose() {
	~/.cargo/bin/cargo install choose
}
install_linux_du-dust() {
	~/.cargo/bin/cargo install du-dust
}
install_linux_onefetch() {
	~/.cargo/bin/cargo install onefetch
}
install_linux_tealdeer() {
	~/.cargo/bin/cargo install tealdeer
}
install_linux_pastel() {
	~/.cargo/bin/cargo install pastel
}
install_linux_hyperfine() {
	~/.cargo/bin/cargo install hyperfine
}
install_linux_git-delta() {
	~/.cargo/bin/cargo install git-delta
}
install_linux_xh() {
	~/.cargo/bin/cargo install xh
}
install_linux_zoxide() {
	~/.cargo/bin/cargo install zoxide
	#zoxide need to configure
}
install_linux_fselect() {
	~/.cargo/bin/cargo install fselect
}
################################ app install/config/upgrade/uninstall functions ################################
#sudo dnf -y remove mesa-libGL mesa-libGL-devel

tmp_dir=${CLONE_PATH}
trap "sudo rm -rf ${tmp_dir}" EXIT

(batch_wrapper "${dnf_apps[@]}")
(batch_wrapper "${customized_apps[@]}")
