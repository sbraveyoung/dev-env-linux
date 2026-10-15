#!/usr/bin/env bash
# Optional integrations must not prevent a fresh shell from starting.
if command -v thefuck >/dev/null 2>&1; then
  eval "$(thefuck --alias 2>/dev/null)"
fi
for integration in "$HOME/.fzf.bash" "$HOME/.autojump/etc/profile.d/autojump.sh" \
  "$HOME/.cargo/env" "${APP_PATH}/git-flow-completion/git-flow-completion.bash" \
  "${APP_PATH}/managed/git-flow-completion/source/git-flow-completion.bash" \
  "${APP_PATH}/managed/z/source/z.sh" \
  /usr/share/doc/fzf/examples/key-bindings.bash /usr/share/doc/fzf/examples/completion.bash; do
  if [[ -s "$integration" ]]; then
    # shellcheck source=/dev/null
    source "$integration"
  fi
done
set -o vi

export PATH="$BIN_PATH:$PATH"
