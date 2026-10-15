"""macOS TODO flows tested on Linux with disposable homes and external-tool substitutes."""
import json
import os
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class MacTodoTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='dev-env-mac-todo-');self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name)
        self.env={**os.environ,'HOME':str(self.work),'REPO':str(ROOT),'APP_PATH':str(self.work/'state'),
                  'BIN_PATH':str(self.work/'bin'),'DEV_ENV_APPLICATIONS_DIR':str(self.work/'Applications')}
        self.config=json.loads((ROOT/'config/software.json').read_text())

    def hook(self,body):
        return subprocess.run(['bash','-c','''source "$REPO/scripts/common_defines.sh"
OPTIONAL=false; WITH_LINUX=false; ENABLE_APPS=(); DISABLE_APPS=(); ONLY_APPS=()
batch_wrapper() { :; }
brew() { printf '%s\\n' "$*" >> "$HOME/brew-calls"; [[ $1 != list ]]; }
source "$REPO/scripts/setup_macos_apps.sh"
'''+body],env=self.env,cwd=self.work,capture_output=True,text=True,timeout=10)

    def test_he3_uses_official_tap_even_when_optional_group_is_not_selected(self):
        result=self.hook('install_darwin_He3')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((self.work/'brew-calls').read_text().splitlines(),['list he3','tap he3-app/he3','install he3'])

    def test_vscode_settings_and_cli_preserve_existing_user_files(self):
        bundle=self.work/'Applications/Visual Studio Code.app/Contents/Resources/app/bin';bundle.mkdir(parents=True)
        (bundle/'code').write_text('cli')
        result=self.hook('config_darwin_visual-studio-code')
        self.assertEqual(result.returncode,0,result.stderr)
        settings=self.work/'Library/Application Support/Code/User/settings.json'
        self.assertIn('editor.fontFamily',json.loads(settings.read_text()))
        self.assertEqual((self.work/'bin/code').resolve(),bundle/'code')
        settings.write_text('// user JSONC\n{"custom":true,}\n')
        (self.work/'bin/code').unlink();(self.work/'bin/code').write_text('user-cli')
        result=self.hook('config_darwin_visual-studio-code')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(settings.read_text(),'// user JSONC\n{"custom":true,}\n')
        self.assertEqual((self.work/'bin/code').read_text(),'user-cli')

    def test_kitty_config_is_created_and_does_not_replace_user_config(self):
        result=self.hook('config_darwin_kitty')
        self.assertEqual(result.returncode,0,result.stderr)
        path=self.work/'.config/kitty/kitty.conf'
        self.assertTrue(path.is_file(),'kitty configuration was not created')
        self.assertIn('font_family',path.read_text())
        path.write_text('user-customization\n')
        result=self.hook('config_darwin_kitty')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(path.read_text(),'user-customization\n')

    def test_qt_application_receipts_are_checked_despite_old_success_cache(self):
        result=self.hook('''CACHE_FILE="$HOME/cache"
printf '%s\\n' "install_darwin_H264Naked_$HOME" > "$CACHE_FILE"
macos_qt_app() { printf '%s\\n' "$*" >> "$HOME/receipt-calls"; }
install darwin "$HOME" H264Naked
install darwin "$HOME" H264Naked
[[ $(wc -l < "$HOME/receipt-calls") == 2 ]]
''')
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)

    def qt_fixture(self):
        # Real installer state and activation; only Git/Qt/make/brew are external substitutes.
        external=self.work/'external';external.mkdir()
        fake=external/'tool'
        fake.write_text('''#!/usr/bin/env python3
import os,sys,plistlib
from pathlib import Path
name=Path(sys.argv[0]).name;args=sys.argv[1:]
if name=='brew' and args[:1]==['--prefix']: print(Path(os.environ['HOME'])/'qt');sys.exit(0)
if name=='git' and args[:1]==['rev-parse']: print('a'*40);sys.exit(0)
if name=='qmake':
 bundle=Path.cwd()/'Demo.app';exe=bundle/'Contents/MacOS/Demo';exe.parent.mkdir(parents=True)
 exe.write_text('new application');exe.chmod(0o755)
 with (bundle/'Contents/Info.plist').open('wb') as output:plistlib.dump({'CFBundleExecutable':'Demo'},output)
if name=='macdeployqt' and os.environ.get('FAIL_DEPLOY')=='yes':sys.exit(7)
''');fake.chmod(0o755)
        for name in ['brew','git','make']:(external/name).symlink_to(fake)
        qt=self.work/'qt/bin';qt.mkdir(parents=True)
        for name in ['qmake','macdeployqt']:(qt/name).symlink_to(fake)
        self.env['PATH']=str(external)+':'+os.environ['PATH']
        self.config['apps']['demo-mac']={'darwin':{'backend':'hook','installer':'qt','source_url':'https://example.invalid/demo.git',
            'revision':'a'*40,'project':'Demo.pro','bundle':'Demo.app','qt_package':'qt@5','brew_dependencies':['qt@5']}}
        self.path=self.work/'catalog.json';self.write_config()
        self.env['DEV_ENV_SOFTWARE_CATALOG']=str(self.path)

    def write_config(self):self.path.write_text(json.dumps(self.config))

    def bundle(self,operation):
        return subprocess.run(['python3',str(ROOT/'scripts/macos_bundle.py'),'demo-mac',operation],
            env=self.env,cwd=self.work,capture_output=True,text=True,timeout=8)

    def test_qt_install_upgrade_rollback_uninstall_owns_only_its_link(self):
        self.qt_fixture()
        result=self.bundle('install');self.assertEqual(result.returncode,0,result.stderr)
        link=self.work/'Applications/Demo.app';first=link.resolve()
        self.assertEqual((link/'Contents/MacOS/Demo').read_text(),'new application')
        self.config['apps']['demo-mac']['darwin']['revision']='b'*40;self.write_config()
        # Have the external Git report the selected checkout.
        tool=self.work/'external/tool';tool.write_text(tool.read_text().replace("print('a'*40)","print('b'*40)"))
        result=self.bundle('upgrade');self.assertEqual(result.returncode,0,result.stderr)
        self.assertNotEqual(link.resolve(),first)
        result=self.bundle('rollback');self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(link.resolve(),first)
        result=self.bundle('uninstall');self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse(link.is_symlink());self.assertTrue(first.is_dir())

    def test_qt_failed_deploy_does_not_publish_partial_app(self):
        self.qt_fixture();self.env['FAIL_DEPLOY']='yes'
        result=self.bundle('install')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('exit status 7',result.stderr)
        self.assertFalse((self.work/'Applications/Demo.app').exists())
        self.assertFalse((self.work/'state/macos/demo-mac/current.json').exists())

    def test_qt_installer_refuses_unmanaged_application(self):
        self.qt_fixture();app=self.work/'Applications/Demo.app';app.mkdir(parents=True);(app/'user').write_text('keep')
        result=self.bundle('install')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('unmanaged',result.stderr)
        self.assertEqual((app/'user').read_text(),'keep')

    def test_qt_catalog_rejects_unsafe_project_paths_before_install(self):
        self.qt_fixture();self.config['apps']['demo-mac']['darwin']['project']='../../escape.pro';self.write_config()
        result=self.bundle('install')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('project',result.stderr)
        self.assertFalse((self.work/'state').exists())
