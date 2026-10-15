"""macOS hook logic tested with fake brew inside Linux, never on a Mac host."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(sys.platform=='linux','macOS mocks run only in isolated Linux')
class MacHookTests(unittest.TestCase):
    def test_system_setup_preserves_security_checks_and_private_directory_permissions(self):
        with tempfile.TemporaryDirectory(prefix='dev-env-mac-system-') as directory:
            work=Path(directory)
            body='''source "$REPO/scripts/common_defines.sh"
execute_if_not_success() { "$@"; }
sudo() { printf '%s\\n' "$*" >> "$HOME/sudo-calls"; }
defaults() { printf '%s\\n' "$*" >> "$HOME/defaults-calls"; }
source "$REPO/scripts/setup_macos_system.sh"
'''
            result=subprocess.run(['bash','-c',body],cwd=work,
                env={**os.environ,'REPO':str(ROOT),'HOME':str(work),
                     'CODE_PATH':str(work/'code'),'GOPATH':str(work/'code'),
                     'CLONE_PATH':str(work/'.local/share/dev-env-linux/src'),
                     'APP_PATH':str(work/'.local/share/dev-env-linux/app'),'BIN_PATH':str(work/'.local/bin')},
                capture_output=True,text=True,timeout=5)
            self.assertEqual(result.returncode,0,result.stderr)
            calls=(work/'defaults-calls').read_text()
            self.assertIn('com.apple.dock autohide -bool true',calls)
            self.assertNotIn('LSQuarantine',calls)
            self.assertNotIn('skip-verify',calls)
            privileged=(work/'sudo-calls').read_text() if (work/'sudo-calls').exists() else ''
            self.assertNotIn('chmod a+w',privileged)
            for name in ['code','.local/share/dev-env-linux/src','.local/share/dev-env-linux/app','.local/bin']:
                self.assertTrue((work/name).is_dir(),name)

    def run_hook(self,body,installed=True,install_status=0):
        with tempfile.TemporaryDirectory(prefix='dev-env-mac-mock-') as directory:
            work=Path(directory)
            preamble='''source "$REPO/scripts/common_defines.sh"
set +x
OPTIONAL=false; WITH_LINUX=false
ENABLE_APPS=(); DISABLE_APPS=(); ONLY_APPS=()
printf2stdout() { :; }; printf2stderr() { :; }
batch_wrapper() { :; }
brew() {
  printf '%s\\n' "$*" >> "$HOME/brew-calls"
  case "$1" in
    list) [[ $FAKE_INSTALLED == true ]] ;;
    install) echo 'fake install error'; return "$FAKE_INSTALL_STATUS" ;;
    *) return 0 ;;
  esac
}
source "$REPO/scripts/setup_macos_apps.sh"
set +e
'''
            result=subprocess.run(['bash','-c',preamble+body],cwd=work,
                env={**os.environ,'REPO':str(ROOT),'HOME':str(work),
                     'FAKE_INSTALLED':str(installed).lower(),'FAKE_INSTALL_STATUS':str(install_status)},
                capture_output=True,text=True,timeout=5)
            calls=(work/'brew-calls').read_text().splitlines() if (work/'brew-calls').exists() else []
            return result,calls

    def test_installed_brew_app_upgrades_and_uninstalls(self):
        result,calls=self.run_hook('upgrade_darwin_tmux; uninstall_darwin_tmux')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(calls,['list tmux','upgrade tmux','list tmux','uninstall tmux'])

    def test_missing_brew_app_is_not_upgraded_or_uninstalled(self):
        result,calls=self.run_hook('upgrade_darwin_tmux; uninstall_darwin_tmux',installed=False)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(calls,['list tmux','list tmux'])

    def test_installed_brew_app_is_not_reinstalled(self):
        result,calls=self.run_hook('install_darwin_tmux')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(calls,['list tmux'])

    def test_failed_install_returns_to_caller_without_changing_trap_or_errexit(self):
        result,calls=self.run_hook('''trap ':' RETURN
before=$(trap -p RETURN)
install_darwin_tmux
status=$?
[[ $status == 7 && $- != *e* && $(trap -p RETURN) == "$before" ]]
''',installed=False,install_status=7)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(calls,['list tmux','install tmux'])

    def test_successful_install_preserves_callers_errexit(self):
        result,calls=self.run_hook('''install_darwin_tmux
[[ $- != *e* ]]
''',installed=False)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(calls,['list tmux','install tmux'])
