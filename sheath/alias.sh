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
#alias cd="cdls"
alias mkdir="mkdir_and_cd"
#about git
alias status="git status"
alias branch="git branch"
alias checkout="git checkout \$(git branch -a | fzf)"
alias ..="cd .." #TODO: multi .., such as ....

#bind -x '"\C-l": clear'
#bind 'TAB:menu-complete'
