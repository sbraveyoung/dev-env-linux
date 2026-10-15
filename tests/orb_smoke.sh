#!/usr/bin/env bash
# Execute INSIDE an isolated Ubuntu machine/container, never on the Mac host.
set -euo pipefail
[[ $(uname -s) == Linux ]] || { printf 'smoke test must run in isolated Linux\n' >&2; exit 2; }
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo"
results="$HOME/dev-env-validation-results"
mkdir -p "$results"
export SKIP_VERSION_CHECK=true
source scripts/catalog.sh
catalog_load defaults --platform linux
export GOLANG_VERSION
bash scripts/check.sh >"$results/check.log" 2>&1
bash ./build.sh --only=jq,tree,ripgrep,tmux --timeout=180 >"$results/install.log" 2>&1
bash ./build.sh --only=jq,tree,ripgrep,tmux --skip-system --timeout=120 >"$results/repeat.log" 2>&1
grep -q 'skip:install_linux_tree' "$results/repeat.log"
bash ./build.sh --operator=upgrade --only=tree --skip-system --timeout=120 >"$results/upgrade.log" 2>&1
bash ./build.sh --operator=uninstall --only=tree --skip-system --timeout=120 >"$results/uninstall.log" 2>&1
if command -v tree >/dev/null; then printf 'tree still installed\n' >&2; exit 1; fi
bash ./build.sh --only=tree --skip-system --timeout=120 >"$results/reinstall.log" 2>&1
tree --version >"$results/tree-version.txt"
bash ./build.sh --only=golang,this-repo --skip-system --timeout=180 >"$results/go-config.log" 2>&1
"$HOME/.local/bin/go" version >"$results/go-version.txt"
bash -c 'source "$1/sheath/init.sh"; go version; command -v jq; command -v rg' _ "$repo" >"$results/profile.log"
[[ $(grep -Fc "$repo/sheath/init.sh" "$HOME/.bashrc") -eq 1 ]]
printf 'PASS: install, repeat, upgrade, uninstall/reinstall, ARM Go, shell profile\n'
printf 'Results: %s\n' "$results"
