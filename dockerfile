FROM centos:8
MAINTAINER SmartBrave <SmartBraveCoder@gmail.com>

#build command: docker build -t IMAGE_NAME --build-arg NORMAL_USER=xxx --build-arg NORMAL_PASSWD=xxx --build-arg ROOT_PASSWD=xxx .
ARG  NORMAL_USER=test_user
ARG  NORMAL_PASSWD=test_passwd
ARG  ROOT_PASSWD=root_passwd

ENV GOPATH=/home/$NORMAL_USER/code/ \
    CLONE_PATH=/usr/local/src \
    BIN_PATH=/usr/local

#git clone https://github.com/Bash-it/bash-it ${CLONE_PATH}/bash-it cd ${CLONE_PATH}/bash-it \
#ShellCheck the_silver_searcher fzf insect \
#sudo go get -u -v github.com/liamg/aminal \
#git clone --config transfer.fsckobjects=false --config receive.fsckobjects=false --config fetch.fsckobjects=false https://github.com/github/hub.git ${CLONE_PATH}/hub cd ${CLONE_PATH}/hub make install prefix=${BIN_PATH}/hub ln -s ${BIN_PATH}/hub/bin/hub /usr/local/bin/hub \
#git clone https://github.com/flok99/multitail ${CLONE_PATH}/multitail cd ${CLONE_PATH}/multitail mkdir build cd build cmake .. sudo make install \
#sudo GOPROXY="https://goproxy.io" GO111MODULE=on go get -u -v github.com/mikefarah/yq/v3
#sudo sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" \
#git-flow
#vim-plugins
#host
#FlameGraph
#GitlHEVCAnalyzer
#gor

RUN    dnf -y update \
    && dnf -y install epel-release \
    && dnf -y --enablerepo=PowerTools install libgcc.i686 glibc-devel bison flex texinfo libtool \
          zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel \
          gdbm-devel xz-devel gettext pkg-config autoconf automake txt2man ncurses ncurses-devel \
          tcl-devel net-tools llvm clang-libs clang-devel which libX11-devel libXcursor-devel \
          libXrandr-devel libXinerama-devel mesa-libGL-devel libXi-devel libevent libevent-devel \
          asciidoc pcre-devel xz-devel bind-utils freetype-devel glib2-devel fontconfig-devel \
    && dnf -y --enablerepo=PowerTools install libpng libpng-devel libjpeg-devel ghostscript-devel \
          libtiff-devel libwmf-devel \
    && dnf -y groupinstall "Development Tools" \
    && dnf -y install git sudo gcc gcc-c++ gdb make unzip ctags vim expect passwd wget cmake\
    && dnf -y install perl nodejs rust cargo golang python2 python2-pip python2-devel \
          python3 python3-pip python3-devel ruby lua luajit zsh \
    && ln -s /usr/bin/python3 /usr/bin/python \
       && ln -s /usr/bin/pip3 /usr/bin/pip \
    && sed -i '/Defaults/s/env_reset/\!env_reset/g' /etc/sudoers \
    && useradd --create-home $NORMAL_USER --password $NORMAL_PASSWD && echo "$NORMAL_USER ALL=(ALL) NOPASSWD:ALL" >>/etc/sudoers \
    && echo "root:$ROOT_PASSWD" | chpasswd

RUN    git clone https://github.com/ImageMagick/ImageMagick ${CLONE_PATH}/ImageMagick \
       && cd ${CLONE_PATH}/ImageMagick \
       && ./configure --prefix=${BIN_PATH}/ImageMagick --with-heic=yes --with-jxl=yes --with-jpeg=yes --with-png=yes --with-webp=yes \
       && make -j 10 \
       && make install \
       && ln -s ${BIN_PATH}/bin/magick /usr/local/bin/magick \
       && ln -s ${BIN_PATH}/ImageMagick/bin/animate /usr/local/bin/animate \
       && ln -s ${BIN_PATH}/ImageMagick/bin/compare /usr/local/bin/compare \
       && ln -s ${BIN_PATH}/ImageMagick/bin/composite /usr/local/bin/composite \
       && ln -s ${BIN_PATH}/ImageMagick/bin/conjure /usr/local/bin/conjure \
       && ln -s ${BIN_PATH}/ImageMagick/bin/convert /usr/local/bin/convert \
       && ln -s ${BIN_PATH}/ImageMagick/bin/display /usr/local/bin/display \
       && ln -s ${BIN_PATH}/ImageMagick/bin/identify /usr/local/bin/identify \
       && ln -s ${BIN_PATH}/ImageMagick/bin/import /usr/local/bin/import \
       && ln -s ${BIN_PATH}/ImageMagick/bin/magick-script /usr/local/bin/magick-script \
       && ln -s ${BIN_PATH}/ImageMagick/bin/mogrify /usr/local/bin/mogrify \
       && ln -s ${BIN_PATH}/ImageMagick/bin/montage /usr/local/bin/montage \
       && ln -s ${BIN_PATH}/ImageMagick/bin/stream /usr/local/bin/stream

RUN    cd ${CLONE_PATH} \
       && curl -OL https://github.com/wagoodman/dive/releases/download/v0.9.2/dive_0.9.2_linux_amd64.rpm \
       && rpm -i dive_0.9.2_linux_amd64.rpm

RUN    wget https://github.com/axel-download-accelerator/axel/releases/download/v2.17.7/axel-2.17.7.tar.gz -O ${CLONE_PATH}/axel-2.17.7.tar.gz \
       && cd ${CLONE_PATH} \
       && tar -zxvf axel-2.17.7.tar.gz \
       && cd axel-2.17.7 \
       && cd ${CLONE_PATH}/axel-2.17.7 \
       && ./configure --prefix=${BIN_PATH}/axel-2.17.7 \
       && make -j 10 \
       && make install \
       && ln -s ${BIN_PATH}/axel-2.17.7/bin/axel /usr/local/bin/axel

RUN    sudo git clone https://github.com/jarun/bcal ${CLONE_PATH}/bcal \
       && cd ${CLONE_PATH}/bcal \
       && make -j 10 \
       && make strip install

RUN    sudo git clone https://github.com/so-fancy/diff-so-fancy ${CLONE_PATH}/diff-so-fancy \
       && cd ${CLONE_PATH}/diff-so-fancy \
       && ln -s diff-so-fancy /usr/local/bin/diff-so-fancy

RUN    git clone https://github.com/clvv/fasd ${CLONE_PATH}/fasd \
       && cd ${CLONE_PATH}/fasd \
       && make install

RUN    git clone https://github.com/dylanaraps/fff ${CLONE_PATH}/fff \
       && cd ${CLONE_PATH}/fff \
       && make PREFIX=${BIN_PATH}/fff install \
       && ln -s ${BIN_PATH}/fff/bin/fff /usr/local/bin/fff

RUN    git clone https://github.com/golbin/git-commander ${CLONE_PATH}/git-commander \
       && cd ${CLONE_PATH}/git-commander \
       && npm -g install blessed lodash git-commander

RUN    git clone https://github.com/hishamhm/htop ${CLONE_PATH}/htop \
       && cd ${CLONE_PATH}/htop \
       && ./autogen.sh \
       && ./configure --prefix=${BIN_PATH}/htop \
       && make -j 10 \
       && make install \
       && ln -s ${BIN_PATH}/htop/bin/htop /usr/local/bin/htop

RUN    curl -L https://bit.ly/glances | /bin/bash

RUN    git clone https://github.com/stedolan/jq ${CLONE_PATH}/jq \
       && cd ${CLONE_PATH}/jq \
       && git submodule update --init \
       && autoreconf -fi \
       && ./configure --prefix=${BIN_PATH}/jq --with-oniguruma=builtin \
       && make -j 10 \
       && make check \
       && make install \
       && ln -s ${BIN_PATH}/jq/bin/jq /usr/local/bin/jq

RUN    git clone https://github.com/hackerb9/lsix ${CLONE_PATH}/lsix \
       && cd ${CLONE_PATH}/lsix \
       && ln -s ${CLONE_PATH}/lsix /usr/local/bin/lsix

RUN    git clone https://github.com/facebook/PathPicker ${CLONE_PATH}/PathPicker \
       && cd ${CLONE_PATH}/PathPicker \
       && ln -s fpp /usr/local/bin/fpp

RUN    git clone https://github.com/jonas/tig ${CLONE_PATH}/tig \
       && cd ${CLONE_PATH}/tig \
       && ./configure LDFLAGS=-L/usr/lib64 CPPFLAGS=-I/usr/include
       && make prefix=${BIN_PATH}/tig \
       && make install prefix=${BIN_PATH}/tig \
       && ln -s ${BIN_PATH}/tig/bin/tig /usr/local/bin/tig

RUN    git clone https://github.com/tmux/tmux ${CLONE_PATH}/tmux \
       && cd ${CLONE_PATH}/tmux \
       && sh autogen.sh \
       && ./configure --prefix=${BIN_PATH}/tmux \
       && make -j 10 \
       && make install \
       && ln -s ${BIN_PATH}/tmux/bin/tmux /usr/local/bin/tmux

RUN    git clone https://github.com/andreafrancia/trash-cli ${CLONE_PATH}/trash-cli \
       && cd ${CLONE_PATH}/trash-cli \
       && python setup.py install

RUN    git clone https://github.com/vifm/vifm ${CLONE_PATH}/vifm \
       && cd ${CLONE_PATH}/vifm \
       && ./scripts/fix-timestamps \
       && ./configure --prefix=${BIN_PATH}/vifm \
       && make \
       && make install \
       && ln -s ${BIN_PATH}/vifm/bin/vifm /usr/local/bin/vifm

RUN    git clone https://github.com/ccache/ccache ${CLONE_PATH}/ccache \
       && cd ${CLONE_PATH}/ccache \
       && ./autogen.sh \
       && ./configure --prefix=${BIN_PATH}/ccache --with-libzstd-from-internet --with-libb2-from-internet \
       && make -j 10 \
       && make install \
       && ln -s ${BIN_PATH}/ccache/bin/ccache /usr/local/bin/ccache

RUN    git clone https://github.com/mptre/yank ${CLONE_PATH}/yank \
       && cd ${CLONE_PATH}/yank \
       && make PREFIX=${BIN_PATH}/yank install \
       && ln -s ${BIN_PATH}/yank/bin/yank /usr/local/bin/yank

RUN    cd ${CLONE_PATH} \
       && wget https://github.com/sharkdp/insect/releases/download/v5.3.0/insect-linux-x64 \
       && ln -s ./insect-linux-x64 /usr/local/bin/insect

RUN    cd ${CLONE_PATH} \
       && wget https://github.com/koalaman/shellcheck/releases/download/stable/shellcheck-stable.linux.x86_64.tar.xz \
       && tar xf shellcheck-stable.linux.x86_64.tar.xz \
       && ln -s ./shellcheck-stable/shellcheck /usr/local/bin/shellcheck

RUN    cd ${CLONE_PATH} \
       && curl -OL https://raw.github.com/nvie/gitflow/develop/contrib/gitflow-installer.sh \
       && chmod +x gitflow-installer.sh \
       && REPO_HOST=git@github.com:nvie/gitflow ./gitflow-installer.sh

RUN    git clone https://github.com/flok99/multitail ${CLONE_PATH}/multitail \
       && cd ${CLONE_PATH}/multitail \
       && mkdir build \
       && cd build \
       && cmake .. \
       && make install

RUN    git clone https://github.com/ggreer/the_silver_searcher ${CLONE_PATH}/the_silver_searcher \
       && cd ${CLONE_PATH}/the_silver_searcher \
       && ./build.sh \
       && make install

RUN    git clone https://github.com/beyondgrep/ack2 ${CLONE_PATH}/ack2 \
       && cpan install File::Next \
       && cd ${CLONE_PATH}/ack2 \
       && perl Makefile.PL \
       && make \
       && make test \
       && make install

RUN    git clone https://git.ffmpeg.org/ffmpeg.git ${CLONE_PATH}/ffmpeg \
       && cd ${CLONE_PATH}/ffmpeg \
       && ./configure --prefix=${BIN_PATH}/ffmpeg --enable-openssl --disable-x86asm \
       && make -j 10 \
       && make install \
       && ln -s ${BIN_PATH}/ffmpeg/bin/ffmpeg /usr/local/bin/ffmpeg \
       && ln -s ${BIN_PATH}/ffmpeg/bin/ffprobe /usr/local/bin/ffprobe

#    && git clone https://github.com/neovim/neovim ${CLONE_PATH}/neovim \
#       && cd ${CLONE_PATH}/neovim \
#       && make CMAKE_INSTALL_PREFIX=${BIN_PATH}/neovim \
#       && make install \
#       && ln -s ${BIN_PATH}/neovim/bin/neovim /usr/local/bin/neovim \

#python
RUN    pip3 install git+https://github.com/jeffkaufman/icdiff.git \
    && pip3 install iredis ranger-fm mdv thefuck mycli asciinema http-prompt \
    && pip3 install --upgrade httpie \
    && pip2 install pyotp

#nodejs
RUN    npm install -g fx fx-completion cloc

#go
RUN    cd ${CLONE_PATH} \
       && wget https://dl.google.com/go/go1.14.3.linux-amd64.tar.gz \
       && tar -zxvf go1.14.3.linux-amd64.tar.gz -C ${BIN_PATH} \
       && ln -s ${BIN_PATH}/go/bin/go /usr/local/bin/go \
       && ln -s ${BIN_PATH}/go/bin/gofmt /usr/local/bin/gofmt \
    && mkdir ${BIN_PATH}/gopath \
    && GOPATH=${BIN_PATH}/gopath GO111MODULE=on GOPROXY=https://goproxy.io go get -u -v github.com/tomnomnom/gron \
    && GOPATH=${BIN_PATH}/gopath go get -u -v github.com/jingweno/ccat \
    && GOPATH=${BIN_PATH}/gopath go get -u -v github.com/go-delve/delve/cmd/dlv \
    && GOPATH=${BIN_PATH}/gopath go get -u -v github.com/peco/peco \
    && GOPATH=${BIN_PATH}/gopath GO111MODULE=on GOPROXY=https://goproxy.io go get -v github.com/mikefarah/yq/v3 \
    && GOPATH=${BIN_PATH}/gopath go get -u -v github.com/liamg/aminal

RUN    chmod a+w ${CLONE_PATH} \
       && chmod a+w ${BIN_PATH}

RUN    usermod -u 501 $NORMAL_USER
USER   $NORMAL_USER
WORKDIR /home/$NORMAL_USER
RUN    ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa

RUN    git clone https://github.com/wting/autojump ${CLONE_PATH}/autojump \
       && cd ${CLONE_PATH}/autojump \
       && SHELL=/bin/bash sudo ./install.py

#rust
RUN    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs > ${CLONE_PATH}/rustup-init.sh \
       && chmod +x ${CLONE_PATH}/rustup-init.sh \
       && ${CLONE_PATH}/rustup-init.sh -y

RUN    ~/.cargo/bin/cargo install --git https://github.com/Peltoche/lsd.git --branch master \
    && ~/.cargo/bin/cargo install --git https://github.com/o2sh/onefetch.git --branch master \
    && ~/.cargo/bin/cargo install broot exa fd-find hexyl ripgrep sd bat \
    && ~/.cargo/bin/cargo install tealdeer

RUN    git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf \
       && ~/.fzf/install \
    && git clone --depth=1 https://github.com/amix/vimrc.git ~/.vim_runtime \
       && sh ~/.vim_runtime/install_awesome_vimrc.sh

RUN    sudo dnf -y install privoxy initscripts cscope
#RUN    sudo sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" \
#    && git clone --depth=1 https://github.com/Bash-it/bash-it.git ${CLONE_PATH}/bash-it \
#       && cd ${CLONE_PATH} \
#       && ./bash-it/install.sh -s

#figlet/ncdu/nnn/pastel/yapf/bench/grv/pomo/cheat/prettyping/cheat.sh/cli-github/terminal_markdown_viewer/dstat/kakoune/https://github.com/alebcay/awesome-shell/ack,sz/rz,fuck,j/mytop/atop/vtop/gtop/gotop/ptop/hegemon,ranger/fd/svg-term/sshrc/github.com/rupa/z,github.com/rupa/v/script/scriptreplay,fortune,trans,bro/alacritty,/hyperfine/startship,file.shell,starship,ctop,lazydocket,colordiff,httpie,tldr,manimlib

USER    root
WORKDIR /
CMD    /usr/bin/bash
