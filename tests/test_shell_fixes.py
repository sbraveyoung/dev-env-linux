import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ShellFixTests(unittest.TestCase):
    def run_shell(self, body, timeout=5):
        with tempfile.TemporaryDirectory(prefix='dev-env-fix-') as work:
            return subprocess.run(['bash', '-c', body], cwd=work,
                env={**os.environ, 'REPO': str(ROOT), 'HOME': work},
                capture_output=True, text=True, timeout=timeout)

    def ok(self, body):
        result = self.run_shell(body)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_smart_cp_creates_nested_destination_with_spaces(self):
        self.ok('''source "$REPO/sheath/functions.sh"
echo ok > 'source file'
smart_cp 'source file' 'nested path/child/dest file'
[[ "$(cat 'nested path/child/dest file')" == ok ]]
''')

    def test_env_save_restore_preserves_literal_value(self):
        self.ok('''source "$REPO/sheath/functions.sh"
SAMPLE='a b; $(touch injected)'
save_origin_env SAMPLE
SAMPLE=changed
restore_origin_env SAMPLE
[[ "$SAMPLE" == 'a b; $(touch injected)' && ! -e injected ]]
''')

    def test_save_env_is_exact_idempotent_under_errexit(self):
        self.ok('''source "$REPO/sheath/functions.sh"
set -e
printf 'x.y\\n' | save_env prompt SAMPLE
printf 'x.y\\n' | save_env prompt SAMPLE
printf 'xay\\n' | save_env prompt SAMPLE
[[ "$(wc -l < .env | tr -d ' ')" == 2 ]]
''')

    def test_configuration_loads_without_optional_tools(self):
        self.ok('''source "$REPO/sheath/functions.sh"
set -e
source "$REPO/sheath/configuration.sh"
''')

    def test_aliases_do_not_replace_commands_with_missing_tools(self):
        self.ok('''source "$REPO/sheath/functions.sh"
unalias cat 2>/dev/null || :
source "$REPO/sheath/alias.sh"
if ! command -v bat >/dev/null; then
  ! alias cat >/dev/null 2>&1
fi
''')

    def test_path_preserves_caller_entries(self):
        self.ok('''PATH="/custom-entry:$PATH"
source "$REPO/sheath/environments.sh"
[[ ":$PATH:" == *:/custom-entry:* ]]
''')

    def test_cli_only_selects_apps(self):
        self.ok('''source "$REPO/scripts/cli.sh"
parse_cli --only=jq,tree --skip-system
[[ "${ONLY_APPS[0]}" == jq && "${ONLY_APPS[1]}" == tree && "$SKIP_SYSTEM" == true ]]
''')

    def test_linux_forwarding_preserves_values_and_selection(self):
        self.ok('''source "$REPO/scripts/cli.sh"
source "$REPO/scripts/forward_cli.sh"
parse_cli --only=jq,tree --skip-system '--app_flag=demo=a b=c' --enable-tmux --disable-jq
make_linux_args
[[ "${LINUX_ARGS[*]}" == *'--only=jq,tree'* && "${LINUX_ARGS[*]}" == *'--skip-system'* ]]
[[ "${LINUX_ARGS[${#LINUX_ARGS[@]}-1]}" == '--app_flag=demo=a b=c' ]]
''')

    def test_download_failure_does_not_poison_retry(self):
        self.ok('''source "$REPO/scripts/common_defines.sh"
set +e
mkdir -p bin
printf '%s\n' '#!/usr/bin/env bash' 'echo partial > "$3"' 'exit 7' > bin/wget
chmod +x bin/wget
PATH="$PWD/bin:$PATH"
wget_nx https://example.invalid/file -O output
status=$?
[[ "$status" == 7 && ! -e output ]]
''')

    def test_clone_handles_spaces_and_localizes_variables(self):
        self.ok('''source "$REPO/scripts/common_defines.sh"
args_num=original
local_path=original
git() { mkdir -p "${@: -1}/.git"; }
git_clone_nx example.invalid 'repo path'
[[ -d 'repo path' && "$args_num" == original && "$local_path" == original ]]
''')

    def test_timeout_kills_task_without_false_success(self):
        self.ok('''source "$REPO/scripts/common_defines.sh"
set +e
TIMEOUT=1
worker() { sleep 3; echo incorrect > late; }
run_with_timeout worker
status=$?
[[ "$status" == 124 && ! -e late ]]
''')

    def test_uninstall_invalidates_install_cache(self):
        self.ok('''source "$REPO/scripts/common_defines.sh"
CACHE_FILE="$HOME/cache"
install_linux_demo() { echo installed >> calls; }
uninstall_linux_demo() { :; }
OPERATOR=install
install linux "$HOME" demo
OPERATOR=uninstall
uninstall linux "$HOME" demo
OPERATOR=install
install linux "$HOME" demo
[[ "$(wc -l < calls | tr -d ' ')" == 2 ]]
''')

    def test_non_install_operations_do_not_use_success_cache(self):
        self.ok('''source "$REPO/scripts/common_defines.sh"
CACHE_FILE="$HOME/cache"
OPERATOR=upgrade
worker() { echo run >> calls; }
execute_if_not_success worker
execute_if_not_success worker
[[ "$(wc -l < calls | tr -d ' ')" == 2 && ! -s "$CACHE_FILE" ]]
''')

    def test_managed_installs_recheck_receipts_despite_global_success_cache(self):
        self.ok('''source "$REPO/scripts/common_defines.sh"
CACHE_FILE="$HOME/cache"
OPERATOR=install
declare -A MANAGED_INSTALL_APPS=([demo]=true)
printf '%s\\n' "install_linux_demo_$HOME" > "$CACHE_FILE"
install_linux_demo() { echo checked >> calls; }
install linux "$HOME" demo
install linux "$HOME" demo
[[ "$(wc -l < calls | tr -d ' ')" == 2 ]]
''')
