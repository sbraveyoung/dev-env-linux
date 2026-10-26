"""Install preservation contracts, executed only inside isolated Linux fixtures."""
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(sys.platform=='linux','requires isolated Linux fixtures')
class InstallPreservationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.home=Path(self.temp.name)
        self.env={**os.environ,'HOME':str(self.home),'REPO':str(ROOT),
                  'APP_PATH':str(self.home/'state'),'BIN_PATH':str(self.home/'bin'),
                  'DEV_ENV_APPLICATIONS_DIR':str(self.home/'Applications')}
        self.config=json.loads((ROOT/'config/software.json').read_text())
        self.config['apps']['google-chrome']['darwin'].update(
            app_bundles=['Google Chrome.app'],bundle_ids=['com.google.Chrome'])
        self.catalog=self.home/'catalog.json';self.catalog.write_text(json.dumps(self.config))
        self.env['DEV_ENV_SOFTWARE_CATALOG']=str(self.catalog)

    def bundle(self,name='Google Chrome.app',identifier='com.google.Chrome',root=None):
        app=(root or self.home/'Applications')/name
        executable=app/'Contents/MacOS/app';executable.parent.mkdir(parents=True)
        executable.write_text('existing manual app');executable.chmod(0o755)
        with (app/'Contents/Info.plist').open('wb') as output:
            plistlib.dump({'CFBundleExecutable':'app','CFBundleIdentifier':identifier,'CFBundlePackageType':'APPL'},output)
        return app

    def shell(self,body,installed=False,only='',no_brew=False):
        self.env['FAKE_INSTALLED']=str(installed).lower()
        self.env['ONLY_TEST_APP']=only
        self.env['NO_BREW']=str(no_brew).lower()
        return subprocess.run(['bash','-c',r'''source "$REPO/scripts/common_defines.sh"
OPTIONAL=false; WITH_LINUX=false; ENABLE_APPS=(); DISABLE_APPS=(); ONLY_APPS=()
[[ -z $ONLY_TEST_APP ]] || ONLY_APPS=("$ONLY_TEST_APP")
CACHE_FILE="$HOME/cache"
batch_wrapper() { :; }
brew() {
 printf '%s\n' "$*" >> "$HOME/brew-calls"
 [[ $1 != list || $FAKE_INSTALLED == true ]]
}
command_exist() {
 if [[ $1 == brew && $NO_BREW == true ]]; then return 1; fi
 type "$1" >/dev/null 2>&1
}
curl() { printf 'unexpected network/bootstrap\n' >&2; return 97; }
source "$REPO/scripts/setup_macos_apps.sh"
'''+body],env=self.env,cwd=self.home,capture_output=True,text=True,timeout=15)

    def inventory(self):
        return subprocess.run(['python3',str(ROOT/'scripts/macos_inventory.py'),'google-chrome'],
            env=self.env,capture_output=True,text=True,timeout=5)

    def test_manual_app_skips_hooks_configuration_and_cache(self):
        self.bundle()
        result=self.shell(r'''preinstall_darwin_google-chrome() { touch "$HOME/preinstall"; }
config_darwin_google-chrome() { touch "$HOME/configured"; }
install darwin "$HOME" google-chrome
install darwin "$HOME" google-chrome
''')
        self.assertEqual(result.returncode,0,result.stderr)
        for name in ['brew-calls','preinstall','configured','cache']:
            self.assertFalse((self.home/name).exists(),name)

    def test_direct_hook_does_not_download_or_tap_for_manual_app(self):
        self.bundle();result=self.shell('install_darwin_google-chrome')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse((self.home/'brew-calls').exists())

    def test_brew_existing_app_skips_configuration(self):
        result=self.shell(r'''config_darwin_google-chrome() { touch "$HOME/configured"; }
install darwin "$HOME" google-chrome
''',installed=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse((self.home/'configured').exists())
        self.assertEqual((self.home/'brew-calls').read_text().splitlines(),['list google-chrome'])

    def test_identity_detects_renamed_app(self):
        app=self.bundle(name='My browser.app')
        result=self.inventory();self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),str(app))

    def test_home_app_is_found_with_separate_system_app_root(self):
        self.env['DEV_ENV_APPLICATIONS_DIR']=str(self.home/'SystemApplications')
        app=self.bundle()
        result=self.inventory();self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),str(app))

    def test_same_name_wrong_identity_is_not_installed(self):
        self.bundle(identifier='org.other.app')
        self.assertEqual(self.inventory().returncode,1)

    def test_incomplete_app_is_not_installed(self):
        app=self.bundle();(app/'Contents/MacOS/app').unlink()
        self.assertEqual(self.inventory().returncode,1)

    def test_owned_qt_link_is_not_treated_as_manual(self):
        app=self.bundle(root=self.home/'state/macos/google-chrome/release')
        link=self.home/'Applications/Google Chrome.app';link.parent.mkdir();link.symlink_to(app)
        self.assertEqual(self.inventory().returncode,1)

    def test_existing_manual_app_does_not_bootstrap_homebrew(self):
        self.bundle()
        # command lookup remains real for other tools; brew availability alone is suppressed.
        result=self.shell(r'''install darwin "$HOME" google-chrome''',only='google-chrome',no_brew=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse((self.home/'brew-calls').exists())

    def test_existing_brew_application_can_still_be_explicitly_uninstalled(self):
        result=self.shell('uninstall darwin "$HOME" google-chrome',installed=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((self.home/'brew-calls').read_text().splitlines(),['list google-chrome','uninstall google-chrome'])

    def test_corrupt_plist_does_not_claim_success(self):
        app=self.bundle();(app/'Contents/Info.plist').write_text('<?xml version="1.0"?><plist><dict>broken')
        result=self.inventory()
        self.assertEqual(result.returncode,1,result.stderr)
        self.assertNotIn('Traceback',result.stderr)

    def test_qt_direct_install_preserves_external_app_without_state(self):
        self.config['apps']['demo-mac']={'darwin':{'backend':'hook','installer':'qt','source_url':'https://example.invalid/demo.git',
            'revision':'a'*40,'project':'Demo.pro','bundle':'Demo.app','qt_package':'qt@5','brew_dependencies':['qt@5']}}
        self.catalog.write_text(json.dumps(self.config))
        app=self.bundle(name='Demo.app',identifier='org.demo.app')
        result=subprocess.run(['python3',str(ROOT/'scripts/macos_bundle.py'),'demo-mac','install'],
            env=self.env,capture_output=True,text=True,timeout=5)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse((self.home/'state').exists())
        self.assertEqual((app/'Contents/MacOS/app').read_text(),'existing manual app')
        for operation in ['upgrade','uninstall','rollback']:
            result=subprocess.run(['python3',str(ROOT/'scripts/macos_bundle.py'),'demo-mac',operation],
                env=self.env,capture_output=True,text=True,timeout=5)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('unmanaged',result.stderr)
            self.assertTrue(app.is_dir())

    def test_wetype_input_method_is_detected_before_downloading(self):
        self.config['apps']['wetype']['darwin']['app_directories']=['~/Library/Input Methods']
        self.catalog.write_text(json.dumps(self.config))
        self.bundle(name='WeType.app',identifier='org.fixture.wetype',root=self.home/'Library/Input Methods')
        result=self.shell('install_darwin_wetype "$HOME"')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse((self.home/'brew-calls').exists())

    def test_alacritty_configuration_preserves_existing_user_file(self):
        target=self.home/'.config/alacritty/alacritty.yml';target.parent.mkdir(parents=True)
        target.write_text('user customization\n')
        result=self.shell('fc-cache() { :; }; config_darwin_alacritty')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(target.read_text(),'user customization\n')

    def linux_hook(self,body):
        return subprocess.run(['bash','-c',r'''source "$REPO/scripts/common_defines.sh"
OPTIONAL=false; ENABLE_APPS=(); DISABLE_APPS=(); ONLY_APPS=(golang)
DISTRO_PKG_APPS=(); DISTRO_OPTIONAL_PKG_APPS=(); SKIP_VERSION_CHECK=true
CLONE_PATH="$HOME/sources"; CACHE_FILE="$HOME/cache"; GOLANG_VERSION=1.2.3
batch_wrapper() { :; }
source "$REPO/scripts/setup_linux_apps.sh"
'''+body],env=self.env,cwd=self.home,capture_output=True,text=True,timeout=10)

    def test_go_sdk_refuses_to_replace_user_command(self):
        binary=self.home/'bin/go';binary.parent.mkdir();binary.write_text('user Go command')
        release=self.home/'state/golang-1.2.3/go/bin';release.mkdir(parents=True)
        (release/'go').write_text('download not needed');(release/'go').chmod(0o755)
        result=self.linux_hook('install_linux_golang')
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(binary.read_text(),'user Go command')
        self.assertFalse((self.home/'state/go').exists())

    def test_go_uninstall_preserves_unmanaged_sdk_link(self):
        other=self.home/'my-go';other.mkdir();state=self.home/'state';state.mkdir()
        link=state/'go';link.symlink_to(other)
        binary=self.home/'bin/go';binary.parent.mkdir();binary.symlink_to(link/'bin/go')
        result=self.linux_hook('uninstall_linux_golang')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(),other)
        self.assertTrue(binary.is_symlink())

    def test_go_uninstall_preserves_user_sdk_directory_and_command_links(self):
        sdk=self.home/'state/go/bin';sdk.mkdir(parents=True)
        (sdk/'go').write_text('user SDK')
        binary=self.home/'bin/go';binary.parent.mkdir();binary.symlink_to(sdk/'go')
        result=self.linux_hook('uninstall_linux_golang')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue(binary.is_symlink())
        self.assertEqual(binary.read_text(),'user SDK')

    def test_stale_wetype_cache_does_not_hide_missing_installer(self):
        result=self.shell(r'''CLONE_PATH="$HOME"; WETYPE_VERSION=1.0_1
printf '%s\n' "install_darwin_wetype_$HOME" > "$CACHE_FILE"
wget_nx() { touch "$HOME/download-attempted"; return 37; }
install darwin "$HOME" wetype
''')
        self.assertEqual(result.returncode,37,result.stderr)
        self.assertTrue((self.home/'download-attempted').exists())

    def test_inventory_error_stops_before_hooks_and_cache(self):
        result=self.shell(r'''darwin_existing_bundle() { return 2; }
preinstall_darwin_google-chrome() { touch "$HOME/preinstall"; }
install darwin "$HOME" google-chrome
''')
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertFalse((self.home/'preinstall').exists())
        self.assertFalse((self.home/'cache').exists())

    def test_unverified_brew_collision_is_an_error(self):
        result=self.shell(r'''brew() {
 if [[ $1 == list ]]; then return 1; fi
 printf 'It seems there is already an App at /Applications/Google Chrome.app\n'
 return 7
}
install_darwin_google-chrome
''')
        self.assertEqual(result.returncode,7,result.stderr)

    def test_changed_detection_catalog_is_validated_before_writes(self):
        original=self.config['apps']['google-chrome']['darwin'].copy()
        for field,value in [('app_bundles',['../escape.app']),('app_bundles','Chrome.app'),
                            ('bundle_ids',['invalid id']),('app_directories',['~/../outside']),
                            ('app_directories',[2])]:
            with self.subTest(field=field,value=value):
                self.config['apps']['google-chrome']['darwin']=original.copy()
                self.config['apps']['google-chrome']['darwin'][field]=value
                self.catalog.write_text(json.dumps(self.config))
                result=self.inventory()
                self.assertEqual(result.returncode,2,result.stderr)
                self.assertIn(field,result.stderr)
                self.assertNotIn('Traceback',result.stderr)
                self.assertFalse((self.home/'state').exists())
                self.config['apps']['google-chrome']['darwin']=original

    def test_stale_success_cache_does_not_hide_missing_brew_app(self):
        result=self.shell(r'''printf '%s\n' "install_darwin_google-chrome_$HOME" > "$CACHE_FILE"
config_darwin_google-chrome() { :; }
install darwin "$HOME" google-chrome
''')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('install google-chrome',(self.home/'brew-calls').read_text().splitlines())

    def test_repeat_dotfile_install_preserves_edits_and_snapshot(self):
        spec=importlib.util.spec_from_file_location('dotfiles_idempotency',ROOT/'scripts/dotfiles.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.HOME=self.home;module.STATE=self.home/'dotstate';module.FILES={'.gitconfig':'config/.gitconfig'}
        module.apply('install')
        target=self.home/'.gitconfig';target.write_text('my subsequent edits')
        startup=self.home/'.bashrc';startup.write_text('my shell configuration\n')
        before={str(p.relative_to(module.STATE)):p.stat().st_mtime_ns for p in module.STATE.rglob('*')}
        module.apply('install')
        self.assertEqual(target.read_text(),'my subsequent edits')
        self.assertEqual(startup.read_text(),'my shell configuration\n')
        self.assertEqual(before,{str(p.relative_to(module.STATE)):p.stat().st_mtime_ns for p in module.STATE.rglob('*')})
        module.apply('upgrade')
        self.assertEqual(target.read_bytes(),(ROOT/'config/.gitconfig').read_bytes())
