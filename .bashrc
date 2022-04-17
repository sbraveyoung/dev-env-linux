# .bashrc

# Source global definitions
if [ -f /etc/bashrc ]; then
	. /etc/bashrc
fi

#################### functions ####################
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

#smart cd: can import environment variable you need automatically
#maybe https://github.com/hyperupcall/autoenv or https://direnv.net/ is better
scd(){ 
    [ -f .unenv ] && . .unenv
    cd $1
    [ -f .env ] && . .env
}

cdls(){
    cd $1
    exa --all
}

jls(){
    j $1
    exa --all
}

jcurl(){
    curl $1 | jq
}

mkdir_and_cd(){
    dir_count=$#

    mkdir $@
    [ $? -eq 0 ] && cd ${!dir_count} #cd the last dir
}
#################### functions ####################


#################### aliases ####################
alias c="clear"
alias cat="bat"
alias ping="prettyping --nolegend"
alias top="gtop"
#alias ls="ls -a --color=auto"
#alias ls="lsd -a"
alias ls="exa --all"
alias ll="ls -h"
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
alias curl="curlie"
alias cd="cdls"
alias mkdir="mkdir_and_cd"

# fasd
alias a='fasd -a'        # any
alias s='fasd -si'       # show / search / select
alias d='fasd -d'        # directory
alias f='fasd -f'        # file
alias sd='fasd -sid'     # interactive directory selection
alias sf='fasd -sif'     # interactive file selection
alias z='fasd_cd -d'     # cd, same functionality as j in autojump
alias zz='fasd_cd -d -i' # cd with interactive selection
#alias v='f -e vim' # quick opening files with vim
bind -x '"\C-l": clear'
#################### aliases ####################


#################### environments ####################
MY_CODE_PATH=$HOME/code
OPEN_CODE_PATH=/usr/local/src
BIN_PATH=/usr/local/bin

export GOPATH=$MY_CODE_PATH
export GOROOT=/usr/local/app/go
export GOBIN=$BIN_PATH
export GOMODCACHE=$OPEN_CODE_PATH/gomod
export PATH=$HOME/.cargo/bin:$HOME/.autojump/bin:$HOME/.fzf/bin:$HOME/.local/bin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:$GOBIN
export LD_LIBRARY_PATH=/usr/local/app/ImageMagick/lib
#export C_INCLUDE_PATH=
export CPLUS_INCLUDE_PATH=/usr/local/app/ImageMagick/include/ImageMagick-7
export MCFLY_KEY_SCHEME=vim
export MCFLY_FUZZY=true
export MCFLY_RESULTS=50
export BAT_THEME="Coldark-Dark"
export TERM=xterm-256color
# export PS1="\u@\h \W \[\033[31m\][\$(echo_sentence)]\[\033[00m\] \[\033[33m\][\$(echo_date)]\[\033[00m\]\[\033[32m\]\$(parse_git_branch)\[\033[00m\] $"
export PS1="\u@\h \W \[\033[33m\][\$(echo_date)]\[\033[00m\]\[\033[32m\]\$(parse_git_branch)\[\033[00m\] $"
#################### environments ####################


#################### source application config ####################
eval $(thefuck --alias 2>/dev/null)
# eval "$(fasd --init auto)"
# source <(fx-completion --bash)
# source $HOME/.config/broot/launcher/bash/br
# Generated for envman. Do not edit.
# [ -s "$HOME/.config/envman/load.sh" ] && source "$HOME/.config/envman/load.sh"
eval "$(mcfly init bash)"
[ -f ~/.fzf.bash ] && source ~/.fzf.bash
[[ -s $HOME/.autojump/etc/profile.d/autojump.sh ]] && source $HOME/.autojump/etc/profile.d/autojump.sh
. "$HOME/.cargo/env"
set -o vi
#################### source application config ####################
