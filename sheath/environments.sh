#MY_CODE_PATH=$HOME/code
MY_CODE_PATH=/Users/bytedance/code
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
export GIT_TERMINAL_PROMPT=1

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

#export PS1="${PS1_STATUS}\u@\h \W ${PS1_SENTENCE} ${PS1_DATE}${PS1_GIT} \$"
export PS1="${PS1_STATUS}\u@\h \W ${PS1_DATE}${PS1_GIT} \$"
