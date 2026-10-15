#!/usr/bin/env bash
# Never replace a working command with an optional tool that is not installed.
_tool_alias() {
  local executable=${2%% *}
  if command -v "$executable" >/dev/null 2>&1; then
    # Table entries are literal command strings, intentionally captured now.
    # shellcheck disable=SC2139
    alias "$1=$2"
  fi
}
_tool_alias c clear
_tool_alias cat bat
_tool_alias ping 'prettyping --nolegend'
_tool_alias top gtop
if command -v lsd >/dev/null 2>&1; then
  alias ls='lsd --all'
elif command -v exa >/dev/null 2>&1; then
  alias ls='exa --all'
fi
alias ll='ls -lh'
_tool_alias mysql mycli
_tool_alias wget axel
_tool_alias of onefetch
_tool_alias redis-cli iredis
_tool_alias r ranger
_tool_alias curl curlie
if [[ -x "$HOME/.ssh/relay.sh" ]]; then
  alias relay='"$HOME/.ssh/relay.sh"'
  alias ssh=relay
fi
if command -v python3 >/dev/null 2>&1; then
  alias www='python3 -m http.server 8000'
fi
alias mkdir=mkdir_and_cd
alias status='git status'
alias branch='git branch'
if command -v fzf >/dev/null 2>&1; then
  alias checkout='git checkout "$(git branch -a | fzf)"'
fi
alias ..='cd ..'
unset -f _tool_alias
