
eval $(thefuck --alias 2>/dev/null)
# source <(fx-completion --bash)
# source $HOME/.config/broot/launcher/bash/br
# Generated for envman. Do not edit.
# [ -s "$HOME/.config/envman/load.sh" ] && source "$HOME/.config/envman/load.sh"
#eval "$(mcfly init bash)"
[ -f ~/.fzf.bash ] && source ~/.fzf.bash
[[ -s $HOME/.autojump/etc/profile.d/autojump.sh ]] && source $HOME/.autojump/etc/profile.d/autojump.sh
. "$HOME/.cargo/env"
# . ${APP_PATH}/z/z.sh
# source ${APP_PATH}/forgit/forgit
source ${APP_PATH}/git-flow-completion/git-flow-completion.bash
set -o vi
