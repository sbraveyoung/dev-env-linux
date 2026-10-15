import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class ManagedTests(unittest.TestCase):
    def test_declared_legacy_python_script_is_exported(self):
        module=load('managed')
        with tempfile.TemporaryDirectory() as tmp:
            module.BASE=Path(tmp)/'managed';module.BIN=Path(tmp)/'bin'
            app=module.BASE/'ranger-fm';destination=app/'1.9.4';binary=destination/'bin';binary.mkdir(parents=True)
            (binary/'ranger').write_text('legacy script');(binary/'ranger').chmod(0o755)
            spec={'backend':'pip','package':'ranger-fm','bin_scripts':['ranger']}
            def metadata(*args,**kwargs):return SimpleNamespace(stdout='[]' if '-c' in args else '')
            with patch.object(module,'run',side_effect=metadata):record=module.describe(spec,destination,'1.9.4')
            self.assertEqual(record['commands'],{'ranger':'bin/ranger'})
            module.activate(app,destination,record)
            self.assertEqual((module.BIN/'ranger').read_text(),'legacy script')

    def test_checksum_rejects_corruption(self):
        module = load('verified_download')
        with tempfile.TemporaryDirectory() as tmp:
            artifact=Path(tmp)/'artifact';artifact.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):module.verify(artifact,'0'*64)

    def test_uninstall_preserves_unmanaged_link_and_retains_version(self):
        module=load('managed')
        with tempfile.TemporaryDirectory() as tmp:
            module.BASE=Path(tmp)/'app';module.BIN=Path(tmp)/'bin';module.BIN.mkdir()
            app=module.BASE/'gron';release=app/'v1';release.mkdir(parents=True)
            record={'version':'v1','commands':{'gron':'bin/gron'}}
            (app/'current.json').write_text(json.dumps(record))
            (module.BIN/'gron').symlink_to('/usr/bin/true')
            module.operate('gron','uninstall')
            self.assertTrue((module.BIN/'gron').is_symlink())
            self.assertTrue(release.exists())

    def test_activation_refuses_user_file(self):
        module=load('managed')
        with tempfile.TemporaryDirectory() as tmp:
            module.BASE=Path(tmp)/'app';module.BIN=Path(tmp)/'bin';module.BIN.mkdir()
            app=module.BASE/'gron';release=app/'v1';release.mkdir(parents=True)
            (release/'gron').write_text('installed')
            (module.BIN/'gron').write_text('user data')
            with self.assertRaises(RuntimeError):
                module.activate(app,release,{'version':'v1','commands':{'gron':'gron'}})
            self.assertEqual((module.BIN/'gron').read_text(),'user data')

class DotfileTests(unittest.TestCase):
    def test_retired_ssh_target_is_restored_during_configuration_migration(self):
        module=load('dotfiles')
        with tempfile.TemporaryDirectory() as tmp:
            module.HOME=Path(tmp)/'home';module.HOME.mkdir();module.STATE=Path(tmp)/'state'
            ssh=module.HOME/'.ssh';ssh.mkdir()
            retired=ssh/'.ssh_config';retired.write_text('original legacy file')
            active=ssh/'config';active.write_text('original SSH config')
            module.FILES={'.ssh/.ssh_config':'config/.ssh_config'}
            module.apply('install')
            module.FILES={'.ssh/config':'config/.ssh_config'}
            module.apply('upgrade')
            self.assertEqual(retired.read_text(),'original legacy file')
            module.apply('uninstall')
            self.assertEqual(active.read_text(),'original SSH config')

    def test_restore_original_and_preserve_intervening_edits(self):
        module=load('dotfiles')
        with tempfile.TemporaryDirectory() as tmp:
            module.HOME=Path(tmp)/'home';module.HOME.mkdir()
            module.STATE=Path(tmp)/'state'
            original=module.HOME/'.gitconfig';original.write_text('my original config')
            module.apply('install')
            module.apply('upgrade')
            edited=module.HOME/'.tigrc';edited.write_text('user modified')
            module.apply('uninstall')
            self.assertEqual(original.read_text(),'my original config')
            self.assertEqual(edited.read_text(),'user modified')
            self.assertNotIn('sheath/init.sh',(module.HOME/'.bashrc').read_text())

class VersionTests(unittest.TestCase):
    def test_source_release_uses_peeled_commit_of_selected_tag(self):
        module=load('managed')
        tag_object='a'*40;commit='b'*40
        def remote(*args,**kwargs):
            if 'refs/tags/v2.17.13' in args:
                return SimpleNamespace(stdout=f'{tag_object}\trefs/tags/v2.17.13\n{commit}\trefs/tags/v2.17.13^{{}}\n')
            return SimpleNamespace(stdout='c'*40+'\tHEAD\n')
        with patch.object(module,'run',side_effect=remote):
            release=module.version({'backend':'source','package':'https://example.invalid/axel.git','ref':'v2.17.13'})
        self.assertEqual(release,commit)

    def test_rollback_activates_previous_and_updates_lock(self):
        module=load('managed')
        with tempfile.TemporaryDirectory() as tmp:
            module.BASE=Path(tmp)/'app';module.BIN=Path(tmp)/'bin'
            app=module.BASE/'gron'
            for version in ['v1','v2']:
                destination=app/version;destination.mkdir(parents=True)
                (destination/'gron').write_text(version)
            old={'backend':'go','version':'v1','commands':{'gron':'gron'}}
            new={'backend':'go','version':'v2','commands':{'gron':'gron'}}
            module.activate(app,app/'v2',new)
            module.atomic_json(app/'previous.json',old)
            module.operate('gron','rollback')
            self.assertEqual((module.BIN/'gron').read_text(),'v1')
            self.assertEqual(json.loads((app/'lock.json').read_text())['version'],'v1')

    def test_failed_activation_changes_no_other_commands(self):
        module=load('managed')
        with tempfile.TemporaryDirectory() as tmp:
            module.BASE=Path(tmp)/'app';module.BIN=Path(tmp)/'bin';module.BIN.mkdir()
            app=module.BASE/'gron';destination=app/'v1';destination.mkdir(parents=True)
            (destination/'first').write_text('first')
            with self.assertRaises(RuntimeError):
                module.activate(app,destination,{'backend':'go','version':'v1','commands':{'first':'first','missing':'missing'}})
            self.assertFalse((module.BIN/'first').exists())

class RustOwnershipTests(unittest.TestCase):
    def test_uninstall_only_removes_private_sdk_links(self):
        import os
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            work=Path(tmp);home=work/'home';home.mkdir()
            app=work/'app';binary=work/'bin';binary.mkdir()
            private=app/'rust-sdk/bin';private.mkdir(parents=True)
            (home/'.cargo').mkdir();sentinel=home/'.cargo/user-tool';sentinel.write_text('keep')
            (private/'cargo').write_text('sdk')
            (binary/'cargo').symlink_to(private/'cargo')
            (binary/'rustc').symlink_to('/usr/bin/true')
            result=subprocess.run(['bash','-c','source "$SDK_SCRIPT"; uninstall_linux_rust'],
                env={**os.environ,'HOME':str(home),'APP_PATH':str(app),'BIN_PATH':str(binary),
                     'SDK_SCRIPT':str(ROOT/'scripts/rust_sdk.sh')},capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertFalse((binary/'cargo').is_symlink())
            self.assertTrue((binary/'rustc').is_symlink())
            self.assertEqual(sentinel.read_text(),'keep')
