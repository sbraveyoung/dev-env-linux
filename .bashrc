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
    quo=`fortune -s`
    echo $quo
    #echo `trans $quo` # toooooo slow!
}

save_origin_env(){
    eval ORIGIN_$1=\${$1}
}

restore_origin_env(){
    ORIGIN_KEY=`echo ORIGIN_$1`
    eval `echo $1`=${!ORIGIN_KEY}
    unset ORIGIN_$1
}

#smart cd: can import environment variable you need automatically
#maybe https://github.com/hyperupcall/autoenv or https://direnv.net/ is better
scd(){ 
    #TODO: take effect in current dir and sub dir.
    [ -f .unenv ] && . .unenv
    cd $1
    [ -f .env ] && . .env
}

cdls(){
    scd $1
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

#maybe watch command is better!
every(){
    t=$1
    shift

    while true
    do
        $@
        sleep $t
    done
}

echo_last_status(){
    [ $1 -ne 0 ] && echo x || echo y
}

timestamp(){
    date --rfc-3339=s -d @$1
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
alias ll="ls -lh"
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
#about git
alias status="git status"
alias branch="git branch"
alias checkout="git checkout"

bind -x '"\C-l": clear'
#################### aliases ####################


#################### environments ####################
MY_CODE_PATH=$HOME/code
OPEN_CODE_PATH=/usr/local/src
BIN_PATH=/usr/local/bin

export GOPATH=$MY_CODE_PATH
export GOROOT=${APP_PATH}/go
export GOBIN=$BIN_PATH
export GOMODCACHE=$OPEN_CODE_PATH/gomod
export PATH=$HOME/.cargo/bin:$HOME/.autojump/bin:$HOME/.fzf/bin:$HOME/.local/bin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:$GOBIN
export LD_LIBRARY_PATH=${APP_PATH}/ImageMagick/lib:/usr/local/lib:${APP_PATH}/ffmpeg/lib
#export C_INCLUDE_PATH=
export CPLUS_INCLUDE_PATH=${APP_PATH}/ImageMagick/include/ImageMagick-7:${APP_PATH}/ffmpeg/include
export MCFLY_KEY_SCHEME=vim
export MCFLY_FUZZY=true
export MCFLY_RESULTS=50
export BAT_THEME="Coldark-Dark"
export TERM=xterm-256color

## PS1
   COLOR_GRAY='\[\033[1;30m\]'
    COLOR_RED='\[\033[1;31m\]'
  COLOR_GREEN='\[\033[1;32m\]'
 COLOR_YELLOW='\[\033[1;33m\]'
   COLOR_BLUE='\[\033[1;34m\]'
COLOR_MAGENTA='\[\033[1;35m\]'
   COLOR_CYAN='\[\033[1;36m\]'
  COLOR_WHITE='\[\033[1;37m\]'
   COLOR_NONE='\[\033[m\]'

#PS1_USER="${COLOR_MAGENTA}\u${COLOR_NONE}"
#PS1_HOST="${COLOR_CYAN}\h${COLOR_NONE}"
#PS1_PWD="${COLOR_YELLOW}\W${COLOR_NONE}"
PS1_SENTENCE="${COLOR_RED}[\$(echo_sentence)]${COLOR_NONE}"
PS1_DATE="${COLOR_YELLOW}[\$(echo_date)]${COLOR_NONE}"
PS1_GIT="${COLOR_GREEN}\$(parse_git_branch)${COLOR_NONE}"
PS1_STATUS="${COLOR_CYAN}[\$(echo_last_status \$?)]${COLOR_NONE}"

export PS1="${PS1_STATUS}\u@\h \W ${PS1_SENTENCE} ${PS1_DATE}${PS1_GIT} \$"
#################### environments ####################


#################### source application config ####################
eval $(thefuck --alias 2>/dev/null)
# source <(fx-completion --bash)
# source $HOME/.config/broot/launcher/bash/br
# Generated for envman. Do not edit.
# [ -s "$HOME/.config/envman/load.sh" ] && source "$HOME/.config/envman/load.sh"
#eval "$(mcfly init bash)"
[ -f ~/.fzf.bash ] && source ~/.fzf.bash
[[ -s $HOME/.autojump/etc/profile.d/autojump.sh ]] && source $HOME/.autojump/etc/profile.d/autojump.sh
. "$HOME/.cargo/env"
. ${APP_PATH}/z/z.sh
source ${APP_PATH}/forgit/forgit
source ${APP_PATH}/git-flow-completion/git-flow-completion.bash
set -o vi
#################### source application config ####################
