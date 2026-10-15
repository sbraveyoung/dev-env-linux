"""Regression tests; all subprocesses run in disposable directories."""
import os
import json
import sys
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ShellTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix='dev-env-test-')
        self.addCleanup(self.workspace.cleanup)
        self.work = Path(self.workspace.name)

    def run_shell(self, body, common=False, timeout=5):
        preamble = ''
        if common:
            preamble = '''cd "$REPO/scripts"
source ./common_defines.sh
set +x
cd "$WORK"
CACHE_FILE="$WORK/cache"
printf2stdout() { :; }
printf2stderr() { :; }
'''
        result = subprocess.run(
            ['bash', '-c', preamble + body], cwd=self.work,
            env={**os.environ, 'REPO': str(ROOT), 'WORK': str(self.work), 'PYTHON': sys.executable},
            text=True, capture_output=True, timeout=timeout,
        )
        return result

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_common_sources_from_any_directory_without_chdir(self):
        result = self.run_shell('''before="$PWD"
source "$REPO/scripts/common_defines.sh"
set +x
[[ "$PWD" == "$before" ]]
''')
        self.assert_ok(result)

    def test_cache_does_not_match_prefix(self):
        result = self.run_shell('''worker() { echo run >> calls; }
echo worker_extra > "$CACHE_FILE"
execute_if_not_success worker
[[ "$(cat calls)" == run ]]
''', common=True)
        self.assert_ok(result)

    def test_cache_preserves_arguments(self):
        result = self.run_shell('''worker() { printf '%s\\n' "$#" "$@" > args; }
execute_if_not_success worker 'two words' '*' ''
[[ "$(cat args)" == $'3\\ntwo words\\n*' ]]
''', common=True)
        self.assert_ok(result)

    def test_cache_separates_argument_boundaries(self):
        result = self.run_shell('''worker() { echo run >> calls; }
execute_if_not_success worker a_b c
execute_if_not_success worker a b_c
[[ "$(wc -l < calls | tr -d ' ')" == 2 ]]
''', common=True)
        self.assert_ok(result)

    def test_cache_failure_is_not_recorded(self):
        result = self.run_shell('''worker() { return 7; }
set +e
execute_if_not_success worker
status=$?
[[ "$status" == 7 && ! -s "$CACHE_FILE" ]]
''', common=True)
        self.assert_ok(result)

    def test_cache_repeat_skips_success(self):
        result = self.run_shell('''worker() { echo run >> calls; }
execute_if_not_success worker
execute_if_not_success worker
[[ "$(wc -l < calls | tr -d ' ')" == 1 ]]
''', common=True)
        self.assert_ok(result)

    def test_cache_preserves_simple_legacy_hook(self):
        result = self.run_shell('''install_linux_demo() { echo run > calls; }
printf '%s\\n' "install_linux_demo_$WORK" > "$CACHE_FILE"
execute_if_not_success install_linux_demo "$WORK"
[[ ! -e calls ]]
''', common=True)
        self.assert_ok(result)

    def test_cache_does_not_change_errexit_setting(self):
        result = self.run_shell('''worker() { :; }
set +e
execute_if_not_success worker
[[ "$-" != *e* ]]
''', common=True)
        self.assert_ok(result)

    def test_batch_failure_finishes_queue_and_propagates(self):
        result = self.run_shell('''source "$REPO/sheath/functions.sh"
set -e
worker() { echo "$1" >> calls; [[ "$1" != bad ]]; }
batch 1 worker bad good
''')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(sorted((self.work / 'calls').read_text().splitlines()), ['bad', 'good'])

    def test_batch_success_and_item_boundaries(self):
        result = self.run_shell('''source "$REPO/sheath/functions.sh"
worker() { printf '%s\\n' "$1" >> calls; }
batch 2 worker 'one two' three
[[ "$(sort calls)" == $'one two\\nthree' ]]
''')
        self.assert_ok(result)

    def test_batch_empty_queue(self):
        result = self.run_shell('source "$REPO/sheath/functions.sh"\nbatch 2 echo\n')
        self.assert_ok(result)

    def test_batch_rejects_bad_concurrency(self):
        for value in ['0', '-1', 'abc']:
            with self.subTest(value=value):
                result = self.run_shell(f'source "$REPO/sheath/functions.sh"\nbatch {value} echo item\n')
                self.assertNotEqual(result.returncode, 0)

    def test_batch_does_not_overwrite_caller_state(self):
        result = self.run_shell('''source "$REPO/sheath/functions.sh"
cmd=original
arg=original
exec 3> descriptor
worker() { :; }
batch 2 worker one two
[[ "$cmd" == original && "$arg" == original ]]
echo intact >&3
[[ "$(cat descriptor)" == intact ]]
''')
        self.assert_ok(result)

    def test_batch_wrapper_preserves_working_path_spaces(self):
        result = self.run_shell('''OPERATOR=install
SYSTEM=linux
CONCURRENT=1
tmp_dir="$WORK/with spaces"
install() { printf '%s\\n' "$#" "$@" > args; }
batch_wrapper demo
[[ "$(cat args)" == "$(printf '%s\\n' 3 linux "$tmp_dir" demo)" ]]
''', common=True)
        self.assert_ok(result)

    def test_app_scripts_do_not_delete_source_directory(self):
        for platform in ['linux', 'macos']:
            with self.subTest(platform=platform):
                result = self.run_shell(f'''OPTIONAL=false
WITH_LINUX=true
ENABLE_APPS=()
DISABLE_APPS=()
DISTRO_PKG_APPS=(git)
DISTRO_OPTIONAL_PKG_APPS=()
CLONE_PATH="$WORK/sources"
mkdir "$CLONE_PATH"
echo keep > "$CLONE_PATH/existing"
SKIP_VERSION_CHECK=true
command_exist() {{ return 0; }}
printf2stdout() {{ :; }}
batch_wrapper() {{ :; }}
sudo() {{ "$@"; }}
source "$REPO/scripts/setup_{platform}_apps.sh"
''')
                self.assert_ok(result)
                self.assertTrue((self.work / 'sources/existing').exists())

    def test_help_from_outside_repository_has_no_side_effects(self):
        result = self.run_shell('bash "$REPO/build.sh" --help')
        self.assert_ok(result)
        self.assertIn('Usage:', result.stdout)
        self.assertEqual(list(self.work.iterdir()), [])

    def test_cli_rejects_invalid_values_before_setup(self):
        for argument in ['--concurrent=0', '--concurrent=no', '--timeout=0', '--operator=wipe', '--unknown']:
            with self.subTest(argument=argument):
                result = self.run_shell(f'bash "$REPO/build.sh" {argument}')
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('invalid argument:', result.stderr.lower())

    def test_install_failure_does_not_run_configuration(self):
        result = self.run_shell('''install_linux_demo() { return 7; }
config_linux_demo() { echo configured > configured; }
set +e
install linux "$WORK" demo
status=$?
[[ "$status" == 7 && ! -e configured && ! -s "$CACHE_FILE" ]]
''', common=True)
        self.assert_ok(result)

    def test_batch_respects_concurrency_bound(self):
        worker = self.work / 'worker.py'
        worker.write_text('''import fcntl, json, time
from pathlib import Path
state = Path('state.json')
def change(delta):
    with open('lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = json.loads(state.read_text()) if state.exists() else {'active': 0, 'max': 0, 'finished': 0}
        data['active'] += delta
        data['max'] = max(data['max'], data['active'])
        if delta < 0:
            data['finished'] += 1
        state.write_text(json.dumps(data))
change(1)
time.sleep(.1)
change(-1)
''')
        result = self.run_shell('''source "$REPO/sheath/functions.sh"
worker() { "$PYTHON" "$WORK/worker.py" "$1"; }
batch 2 worker one two three four
''')
        self.assert_ok(result)
        data = json.loads((self.work / 'state.json').read_text())
        self.assertEqual(data, {'active': 0, 'max': 2, 'finished': 4})

    def test_cli_clean_cache_targets_repository_not_caller(self):
        import shutil
        copy = self.work / 'repo with spaces'
        (copy / 'scripts').mkdir(parents=True)
        shutil.copy(ROOT / 'build.sh', copy / 'build.sh')
        shutil.copy(ROOT / 'scripts/cli.sh', copy / 'scripts/cli.sh')
        cache = copy / '.repo with spaces'
        cache.write_text('success')
        caller_cache = self.work / '.repo with spaces'
        caller_cache.write_text('keep')
        result = self.run_shell('bash "$WORK/repo with spaces/build.sh" --clean_cache')
        self.assert_ok(result)
        self.assertFalse(cache.exists())
        self.assertEqual(caller_cache.read_text(), 'keep')

    def test_cli_app_flag_preserves_equals_and_spaces(self):
        result = self.run_shell('''source "$REPO/scripts/cli.sh"
parse_cli '--app_flag=wetype=key=a b' '--enable-demo' '--optional=true'
[[ "${APP_FLAG_ARGS[0]}" == 'wetype=key=a b' && "${ENABLE_APPS[0]}" == demo && "$OPTIONAL" == true ]]
''')
        self.assert_ok(result)


if __name__ == '__main__':
    unittest.main(verbosity=2)
