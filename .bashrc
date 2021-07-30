# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

# Uncomment the following line if you don't like systemctl's auto-paging feature:
# export SYSTEMD_PAGER=

set -o vi

[ -f ~/.fzf.bash ] && source ~/.fzf.bash
[[ -s /home/smart/.autojump/etc/profile.d/autojump.sh ]] && source /home/smart/.autojump/etc/profile.d/autojump.sh

# User specific aliases and functions
parse_git_branch(){
    git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ [\1]/'
}

echo_date(){
    date +'%Y/%m/%d %H:%M:%S'
}

echo_sentence(){
    quo="逝者如斯夫,不舍昼夜!"
    # quo=`fortune -s`
    echo $quo
    #echo `trans $quo` # toooooo slow!
}

alias cat="bat"
alias ping="prettyping --nolegend"
alias top="gtop"
#alias ls="ls -a --color=auto"
alias ls="exa --all"
#alias ls="lsd -a"
alias c="clear"
alias mysql="mycli"
alias wget="axel"
alias tig="/usr/local/bin/tig"
alias relay="$HOME/.ssh/relay.sh"
alias ssh="relay"
#alias find=fd
alias www="python -m SimpleHTTPServer 8000"
alias of="onefetch"
alias redis-cli="iredis"
alias r="ranger"
# alias cdls="foo(){ cd '$1'; ls }; foo"
# alias jcurl="foo(){ curl '$1' | jq }; foo"

#### fasd
alias a='fasd -a'        # any
alias s='fasd -si'       # show / search / select
alias d='fasd -d'        # directory
alias f='fasd -f'        # file
alias sd='fasd -sid'     # interactive directory selection
alias sf='fasd -sif'     # interactive file selection
alias z='fasd_cd -d'     # cd, same functionality as j in autojump
alias zz='fasd_cd -d -i' # cd with interactive selection
#alias v='f -e vim' # quick opening files with vim
####
eval $(thefuck --alias 2>/dev/null)
eval "$(fasd --init auto)"
source <(fx-completion --bash)

HOME=/home/smart
CODE_PATH=$HOME/code
export GOPATH=$CODE_PATH
export GOROOT=/usr/local/go
export GOBIN=$GOPATH/bin
#export GO111MODULE=on
export PYENV_ROOT="$HOME/.pyenv"
export PATH=$HOME/.cargo/bin:$HOME/.autojump/bin:$HOME/.fzf/bin:$HOME/.local/bin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:$GOBIN #:$HOME/dockerhome/code/go/bin
export PATH="$PYENV_ROOT/bin:$PATH"
if command -v pyenv 1>/dev/null 2>&1; then
  eval "$(pyenv init -)"
fi
export LD_LIBRARY_PATH=/usr/local/libeventbuild/lib:~/ffmpeg_build/lib
