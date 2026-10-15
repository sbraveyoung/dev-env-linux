"""Declaration consumers: selection, backend precedence, validation and safe shell data."""
import json
import copy
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'scripts/catalog.py'

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name)
        self.config=json.loads((ROOT/'config/software.json').read_text())
        self.path=self.work/'software.json'

    def call(self,*args):
        self.path.write_text(json.dumps(self.config))
        return subprocess.run(['python3',str(CLI),'--config',str(self.path),*args],
                              cwd=self.work,capture_output=True,text=True,timeout=5)

    def test_changed_profile_is_read_without_editing_shell(self):
        self.config['profiles']['linux-default']=['tmux','lazygit']
        result=self.call('profile','linux-default','--shell-var','customized_apps')
        self.assertEqual(result.returncode,0,result.stderr)
        shell=subprocess.run(['bash','-c',result.stdout+'\nprintf "%s\\n" "${customized_apps[@]}"'],capture_output=True,text=True)
        self.assertEqual(shell.stdout.splitlines(),['tmux','lazygit'])

    def test_native_precedence_preserves_fedora_and_el_fallback(self):
        for distro,identity,expected in [('apt','ubuntu','axel'),('dnf','fedora','axel'),('dnf','centos',None)]:
            with self.subTest(identity=identity):
                result=self.call('native','--distro',distro,'--distro-id',identity)
                self.assertEqual(result.returncode,0,result.stderr)
                pairs=dict(line.split('\t') for line in result.stdout.splitlines())
                self.assertEqual(pairs.get('axel'),expected)
                if identity=='fedora':self.assertEqual(pairs['ffmpeg'],'ffmpeg-free')

    def test_sdk_defaults_allow_existing_environment_override(self):
        self.config['apps']['golang']['version']['default']='1.2.3'
        result=self.call('defaults','--platform','linux')
        self.assertEqual(result.returncode,0,result.stderr)
        for existing,want in [('', '1.2.3'),('9.8.7','9.8.7')]:
            shell=subprocess.run(['bash','-c',result.stdout+'\nprintf "%s" "$GOLANG_VERSION"'],
                                 env={**os.environ,'GOLANG_VERSION':existing},capture_output=True,text=True)
            self.assertEqual(shell.returncode,0,shell.stderr)
            self.assertEqual(shell.stdout,want)

    def test_optional_glob_package_is_kept_literal(self):
        (self.work/'libheif-accidental-expansion').touch()
        result=self.call('packages','--distro','dnf')
        self.assertEqual(result.returncode,0,result.stderr)
        shell=subprocess.run(['bash','-c',result.stdout+'\nprintf "%s\\n" "${DISTRO_OPTIONAL_PKG_APPS[@]}"'],cwd=self.work,capture_output=True,text=True)
        self.assertIn('libheif*',shell.stdout.splitlines())
        self.assertNotIn('libheif-accidental-expansion',shell.stdout.splitlines())

    def test_unknown_profile_reference_and_unsafe_id_are_rejected_before_output(self):
        for name in ['missing-app','bad;touch injected']:
            with self.subTest(name=name):
                self.config['profiles']['linux-default']=[name]
                result=self.call('profile','linux-default','--shell-var','customized_apps')
                self.assertNotEqual(result.returncode,0)
                self.assertEqual(result.stdout,'')
                self.assertIn('profile',result.stderr)

    def test_invalid_backend_is_rejected(self):
        self.config['apps']['ccat']['managed']['backend']='typo'
        result=self.call('validate')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('backend',result.stderr)

    def test_invalid_nested_values_report_the_field_without_traceback(self):
        cases=[
            (['profiles'],[], 'profiles'),
            (['drivers','apt'],[], 'drivers.apt'),
            (['backend_dependencies','source'],[], 'backend_dependencies.source'),
            (['apps','ccat','native'],[], 'apps.ccat.native'),
            (['apps','wetype','darwin'],[], 'apps.wetype.darwin'),
            (['apps','golang','version'],[], 'apps.golang.version'),
            (['apps','golang','version','latest'],[], 'apps.golang.version.latest'),
            (['apps','golang','version','default'],123, 'apps.golang.version.default'),
            (['apps','ccat','managed','commands'],[], 'apps.ccat.managed.commands'),
            (['apps','ccat','managed','commands'],{'ccat':'../../outside'}, 'apps.ccat.managed.commands'),
            (['apps','ccat','managed','commands'],{'ccat':'/tmp/tool'}, 'apps.ccat.managed.commands'),
            (['apps','ccat','managed','aliases'],{'../outside':'ccat'}, 'apps.ccat.managed.aliases'),
            (['apps','ccat','managed','bin_scripts'],['../outside'], 'apps.ccat.managed.bin_scripts'),
            (['apps','ccat','managed','verison'],'v1.2.3', 'verison'),
            (['apps','wetype','darwin','implemented'],'false', 'implemented'),
            (['apps','golang','targets'],['arm64'], 'targets'),
            (['bootstrap','homebrew','install_url'],'file:///tmp/install.sh', 'install_url'),
        ]
        original=copy.deepcopy(self.config)
        for path,value,label in cases:
            with self.subTest(path=path,value=value):
                self.config=copy.deepcopy(original);owner=self.config
                for key in path[:-1]:owner=owner[key]
                owner[path[-1]]=value
                result=self.call('validate')
                self.assertEqual(result.returncode,2,result.stderr)
                self.assertEqual(result.stdout,'')
                self.assertNotIn('Traceback',result.stderr)
                self.assertIn(label,result.stderr)

    def test_darwin_profile_requires_a_darwin_installation(self):
        self.config['profiles']['darwin-base']=['ccat']
        result=self.call('macos')
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertEqual(result.stdout,'')
        self.assertIn('darwin-base',result.stderr)
        self.assertNotIn('Traceback',result.stderr)

    def test_missing_required_profile_is_rejected_before_rendering(self):
        del self.config['profiles']['darwin-development']
        result=self.call('defaults','--platform','linux')
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertEqual(result.stdout,'')
        self.assertIn('darwin-development',result.stderr)

    def test_direct_python_consumers_reject_duplicate_keys_before_side_effects(self):
        self.config['apps']['golang']['checksum_url']='file:///nonexistent/catalog-must-be-validated'
        self.path.write_text(json.dumps(self.config).replace('"schema": 1','"schema": 1, "schema": 1',1))
        external=self.work/'external';external.mkdir()
        bash=external/'bash';bash.write_text('#!/bin/sh\nexit 0\n');bash.chmod(0o755)
        for script,args in [('scripts/managed.py',['ccat','rollback']),('scripts/managed_gc.py',['--apply']),
                            ('scripts/export_lock.py',[]),('tests/full_install.py',[]),
                            ('scripts/verified_download.py',['go',str(self.work/'payload'),'1.2.3','arm64'])]:
            with self.subTest(script=script):
                work=self.work/Path(script).stem;work.mkdir()
                result=subprocess.run(['python3',str(ROOT/script),*args],cwd=self.work,
                    env={**os.environ,'DEV_ENV_SOFTWARE_CATALOG':str(self.path),'APP_PATH':str(work/'apps'),
                         'BIN_PATH':str(work/'bin'),'RESULTS_DIR':str(work/'results'),
                         'PATH':str(external)+':'+os.environ['PATH']},
                    capture_output=True,text=True,timeout=8)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('duplicate JSON key',result.stderr)
                self.assertNotIn('Traceback',result.stderr)
                self.assertEqual(result.stdout,'')
                self.assertFalse((work/'apps').exists())
                self.assertFalse((work/'results').exists())

    def test_full_install_honors_alternate_profile_without_unselected_sdks(self):
        self.config['profiles']['linux-default']=['tmux']
        self.path.write_text(json.dumps(self.config));binary=self.work/'bin';binary.mkdir()
        bash=binary/'bash'
        bash.write_text('#!/bin/sh\nprintf "%s\\n" "$@" >> "$HOME/build-args"\n');bash.chmod(0o755)
        result=subprocess.run(['python3',str(ROOT/'tests/full_install.py')],cwd=self.work,
            env={**os.environ,'HOME':str(self.work),'DEV_ENV_SOFTWARE_CATALOG':str(self.path),
                 'RESULTS_DIR':str(self.work/'results'),'PATH':str(binary)+':'+os.environ['PATH']},
            capture_output=True,text=True,timeout=8)
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads((self.work/'results/results.json').read_text())
        self.assertEqual([row['app'] for row in report],['tmux'])
        self.assertIn('--only=tmux',(self.work/'build-args').read_text().splitlines())

    def test_darwin_listing_distinguishes_brew_and_unimplemented_hooks(self):
        result=self.call('list','--platform','darwin')
        self.assertEqual(result.returncode,0,result.stderr)
        rows={row['app']:row for row in json.loads(result.stdout)}
        self.assertEqual(rows['wechat']['version'],'Homebrew managed')
        self.assertEqual(rows['StreamEye']['version'],'not implemented')
        self.assertEqual(rows['wetype']['version'],'0.9.8_201')

    def test_download_template_uses_declared_version_and_arch(self):
        result=self.call('field','golang','download_url','--version','1.2.3','--arch','arm64')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),'https://go.dev/dl/go1.2.3.linux-arm64.tar.gz')

    def test_mac_selection_respects_optional_and_linux_development_choice(self):
        result=self.call('macos','--optional','false','--development','false')
        self.assertEqual(result.returncode,0,result.stderr)
        shell=subprocess.run(['bash','-c',result.stdout+'\nprintf "%s\\n" "${brew_apps[@]}" "${customized_apps[@]}"'],capture_output=True,text=True)
        names=shell.stdout.splitlines()
        self.assertIn('wetype',names);self.assertIn('wechat',names)
        self.assertNotIn('tmux',names);self.assertNotIn('orbstack',names)

    def test_duplicate_json_keys_are_rejected(self):
        self.path.write_text('{"schema":1,"schema":2}')
        result=subprocess.run(['python3',str(CLI),'--config',str(self.path),'validate'],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('duplicate',result.stderr)

    def test_linux_installer_uses_changed_profile_and_native_package(self):
        self.config['apps']['demo']={'native':{'apt':'configured-package'}}
        self.config['profiles']['linux-default']=['demo']
        self.path.write_text(json.dumps(self.config))
        body='''source "$REPO/scripts/common_defines.sh"
OPTIONAL=false; DISTRO=apt; ENABLE_APPS=(); DISABLE_APPS=(); ONLY_APPS=()
DISTRO_PKG_APPS=(); DISTRO_OPTIONAL_PKG_APPS=(); SKIP_SYSTEM=true
pkg_install() { printf '%s\\n' "$@" > "$HOME/package-calls"; }
batch_wrapper() { printf '%s\\n' "$*" >> "$HOME/queues"; }
source "$REPO/scripts/setup_linux_apps.sh"
install_linux_demo
'''
        result=subprocess.run(['bash','-c',body],cwd=self.work,
            env={**os.environ,'HOME':str(self.work),'REPO':str(ROOT),'DEV_ENV_SOFTWARE_CATALOG':str(self.path),'SKIP_VERSION_CHECK':'true'},
            capture_output=True,text=True,timeout=8)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((self.work/'package-calls').read_text().splitlines(),['configured-package'])
        self.assertEqual((self.work/'queues').read_text().splitlines(),['','demo'])

    def test_managed_install_uses_declared_source(self):
        self.config['apps']['ccat']['managed']['package']='example.invalid/ccat'
        self.config['apps']['ccat']['managed']['version']='v9.8.7'
        self.path.write_text(json.dumps(self.config));binary=self.work/'bin';binary.mkdir()
        go=binary/'go'
        go.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$*" > "$HOME/go-calls"\nmkdir -p "$GOBIN"\nprintf tool > "$GOBIN/ccat"\nchmod +x "$GOBIN/ccat"\n');go.chmod(0o755)
        result=subprocess.run(['python3',str(ROOT/'scripts/managed.py'),'ccat','install'],
            env={**os.environ,'HOME':str(self.work),'DEV_ENV_SOFTWARE_CATALOG':str(self.path),
                 'APP_PATH':str(self.work/'apps'),'BIN_PATH':str(binary),'PATH':str(binary)+':'+os.environ['PATH']},
            capture_output=True,text=True,timeout=8)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((self.work/'go-calls').read_text().strip(),'install example.invalid/ccat@v9.8.7')
        self.assertEqual((binary/'ccat').read_text(),'tool')

    def test_changed_source_cannot_silently_activate_an_old_receipt(self):
        self.config['apps']['ccat']['managed']['package']='example.invalid/new-source'
        self.path.write_text(json.dumps(self.config))
        app=self.work/'apps/managed/ccat';version=app/'v1.1.0';(version/'bin').mkdir(parents=True)
        (version/'bin/ccat').write_text('original payload')
        record={'backend':'go','package':'github.com/jingweno/ccat','version':'v1.1.0','schema':4,'commands':{'ccat':'bin/ccat'}}
        (version/'receipt.json').write_text(json.dumps(record));(app/'lock.json').write_text(json.dumps(record))
        result=subprocess.run(['python3',str(ROOT/'scripts/managed.py'),'ccat','install'],
            env={**os.environ,'DEV_ENV_SOFTWARE_CATALOG':str(self.path),'APP_PATH':str(self.work/'apps'),'BIN_PATH':str(self.work/'bin')},
            capture_output=True,text=True,timeout=5)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('source differs',result.stderr)
        self.assertEqual((version/'bin/ccat').read_text(),'original payload')
        self.assertFalse((self.work/'bin/ccat').exists())
