"""Dotfile crash and concurrency behavior in disposable Linux homes."""
import fcntl
import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(sys.platform=='linux','isolated Linux only')
class DotfileTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name);self.home=self.work/'home';self.home.mkdir();self.state=self.work/'state'
        spec=importlib.util.spec_from_file_location('transaction_dotfiles',ROOT/'scripts/dotfiles.py')
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        self.module.HOME=self.home;self.module.STATE=self.state
        self.module.FILES={'.gitconfig':'config/.gitconfig','.tigrc':'config/.tigrc'}
        (self.home/'.gitconfig').write_text('original Git configuration')
        (self.home/'.tigrc').write_text('original Tig configuration')
        (self.home/'.bashrc').write_text('original shell configuration\n')

    def child(self,operation='install',crash='none',popen=False,relative='.gitconfig'):
        code=r'''import importlib.util,json,os,signal,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('dotfiles_child',sys.argv[1]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.HOME=Path(sys.argv[2]);m.STATE=Path(sys.argv[3]);m.FILES=json.loads(sys.argv[6])
real=os.replace
mode=sys.argv[5]
def replace(source,target):
 real(source,target)
 if (mode=='gap' and Path(source)==m.HOME/sys.argv[7]) or (mode=='published' and Path(target)==m.HOME/sys.argv[7]) or (mode=='receipt' and Path(target)==m.STATE/'current.json'):
  os.kill(os.getpid(),signal.SIGKILL)
os.replace=replace
print('ready',flush=True)
m.apply(sys.argv[4])
'''
        args=['python3','-c',code,str(ROOT/'scripts/dotfiles.py'),str(self.home),str(self.state),operation,crash,json.dumps(self.module.FILES),relative]
        if popen:return subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        return subprocess.run(args,capture_output=True,text=True,timeout=8)

    def assert_original(self):
        self.assertEqual((self.home/'.gitconfig').read_text(),'original Git configuration')
        self.assertEqual((self.home/'.tigrc').read_text(),'original Tig configuration')
        self.assertEqual((self.home/'.bashrc').read_text(),'original shell configuration\n')

    def test_uninstall_preserves_user_added_directory_symlink(self):
        self.module.FILES={'.config/nvim':'config/nvim'}
        self.module.apply('install')
        external=self.work/'my-plugins';external.mkdir()
        link=self.home/'.config/nvim/lua/plugins/external';link.symlink_to(external)
        self.module.apply('uninstall')
        self.assertTrue(link.is_symlink())
        self.assertEqual(link.resolve(),external)

    def test_recovery_preserves_directory_symlink_added_after_crash(self):
        self.module.FILES={'.config/nvim':'config/nvim'}
        result=self.child(crash='published',relative='.config/nvim')
        self.assertEqual(result.returncode,-9,result.stderr)
        external=self.work/'my-plugins';external.mkdir()
        link=self.home/'.config/nvim/lua/plugins/external';link.symlink_to(external)
        with self.assertRaises(ValueError):self.module.apply('recover')
        self.assertTrue(link.is_symlink())

    def test_uninstall_preserves_later_tightened_startup_permissions(self):
        path=self.home/'.bashrc';path.chmod(0o644)
        self.module.apply('install');path.chmod(0o600)
        self.module.apply('uninstall')
        self.assertEqual(path.stat().st_mode & 0o777,0o600)
        self.assertNotIn('sheath/init.sh',path.read_text())

    def test_uninstall_preserves_mode_only_edit_to_managed_file(self):
        path=self.home/'.gitconfig'
        self.module.apply('install');path.chmod(0o600)
        self.module.apply('uninstall')
        self.assertEqual(path.stat().st_mode & 0o777,0o600)

    def test_shell_startup_permissions_are_not_widened(self):
        path=self.home/'.bashrc';path.chmod(0o600)
        self.module.apply('install')
        self.assertEqual(path.stat().st_mode & 0o777,0o600)
        self.module.apply('uninstall');self.assert_original()

    def test_originally_absent_startup_file_is_removed_if_unmodified(self):
        path=self.home/'.bashrc';path.unlink()
        self.module.apply('install');self.module.apply('uninstall')
        self.assertFalse(path.exists())

    def test_staging_failure_does_not_modify_live_dotfiles(self):
        real=self.module.copy
        def copy(source,target):
            if source==ROOT/'config/.tigrc':raise OSError('disk failure')
            return real(source,target)
        with patch.object(self.module,'copy',side_effect=copy):
            with self.assertRaises(OSError):self.module.apply('install')
        self.assert_original();self.assertFalse((self.state/'current.json').exists())

    def test_journal_write_failure_removes_prepared_sidecars(self):
        real=os.replace
        def replace(source,target):
            if Path(target)==self.state/'pending.json':raise OSError('journal disk failure')
            return real(source,target)
        with patch.object(os,'replace',side_effect=replace):
            with self.assertRaises(OSError):self.module.apply('install')
        self.assert_original()
        self.assertEqual(list(self.home.rglob('.dev-env-dotfiles-*')),[])

    def test_receipt_failure_rolls_back_all_live_changes(self):
        real=os.replace;failed=False
        def replace(source,target):
            nonlocal failed
            if Path(target)==self.state/'current.json' and not failed:
                failed=True;raise OSError('receipt disk failure')
            return real(source,target)
        with patch.object(os,'replace',side_effect=replace):
            with self.assertRaises(OSError):self.module.apply('install')
        self.assert_original();self.assertFalse((self.state/'current.json').exists())

    def test_killed_between_renames_can_restore_originals(self):
        result=self.child(crash='gap');self.assertEqual(result.returncode,-9,result.stderr)
        self.module.apply('recover')
        self.assert_original();self.assertFalse((self.state/'current.json').exists())
        self.module.apply('install');self.module.apply('uninstall');self.assert_original()

    def test_recovery_refuses_overwriting_edits_made_after_crash(self):
        result=self.child(crash='published');self.assertEqual(result.returncode,-9,result.stderr)
        path=self.home/'.gitconfig';path.write_text('edits after crash')
        with self.assertRaises(ValueError):self.module.apply('recover')
        self.assertEqual(path.read_text(),'edits after crash')
        path.write_bytes((ROOT/'config/.gitconfig').read_bytes())
        self.module.apply('recover');self.assert_original()

    def test_killed_after_receipt_commit_finishes_cleanup_without_rollback(self):
        result=self.child(crash='receipt');self.assertEqual(result.returncode,-9,result.stderr)
        self.module.apply('recover')
        self.assertEqual((self.home/'.gitconfig').read_bytes(),(ROOT/'config/.gitconfig').read_bytes())
        self.assertTrue((self.state/'current.json').exists())
        self.assertFalse((self.state/'pending.json').exists())
        self.assertEqual(list(self.home.rglob('.dev-env-dotfiles-*')),[])
        self.module.apply('uninstall');self.assert_original()

    def test_killed_uninstall_can_be_recovered_and_retried(self):
        self.module.apply('install')
        result=self.child(operation='uninstall',crash='gap');self.assertEqual(result.returncode,-9,result.stderr)
        self.module.apply('recover')
        self.assertEqual((self.home/'.gitconfig').read_bytes(),(ROOT/'config/.gitconfig').read_bytes())
        self.assertTrue((self.state/'current.json').is_file())
        self.module.apply('uninstall');self.assert_original()

    def test_cached_install_still_recovers_interrupted_upgrade(self):
        repo=self.work/'checkout';repo.mkdir()
        for name in ['scripts','sheath','config']:shutil.copytree(ROOT/name,repo/name,ignore=shutil.ignore_patterns('__pycache__'))
        for name in ['build.sh','software.lock.json']:shutil.copy2(ROOT/name,repo/name)
        self.state=self.work/'app/dotfiles';self.module.STATE=self.state
        self.module.apply('install')
        (self.home/'.gitconfig').write_text('user edits before upgrade')
        result=self.child(operation='upgrade',crash='gap');self.assertEqual(result.returncode,-9,result.stderr)
        (repo/'.checkout').write_text('install_linux_this-repo_'+str(self.work/'sources')+'\n')
        env={**os.environ,'HOME':str(self.home),'APP_PATH':str(self.work/'app'),
             'BIN_PATH':str(self.work/'bin'),'CLONE_PATH':str(self.work/'sources')}
        result=subprocess.run(['bash',str(repo/'build.sh'),'--skip-system','--only=this-repo'],
                              env=env,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue((self.home/'.gitconfig').is_file())
        self.assertEqual((self.home/'.gitconfig').read_text(),'user edits before upgrade')
        self.assertFalse((self.state/'pending.json').exists())

    def test_other_process_waits_for_lifecycle_lock(self):
        self.state.mkdir();lock=(self.state/'.transaction.lock').open('a')
        with lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            process=self.child(popen=True)
            try:
                self.assertEqual(process.stdout.readline().strip(),'ready')
                with self.assertRaises(subprocess.TimeoutExpired):process.communicate(timeout=.15)
                self.assert_original()
            finally:
                fcntl.flock(lock,fcntl.LOCK_UN)
                out,error=process.communicate(timeout=8)
            self.assertEqual(process.returncode,0,error)
