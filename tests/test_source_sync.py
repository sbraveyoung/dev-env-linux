"""Guest source delivery contracts, run only inside isolated Linux."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

@unittest.skipUnless(sys.platform=='linux','isolated Linux only')
class SourceSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name);self.guest=self.work/'guest';self.guest.mkdir()
        self.repo=self.work/'repo';(self.repo/'scripts').mkdir(parents=True)
        for name in ['sheath','config','tests']:(self.repo/name).mkdir()
        (self.repo/'software.lock.json').write_text('{"ccat":{"version":"v1.0.0"}}\n')
        (self.repo/'build.sh').write_text('#!/usr/bin/env bash\n[[ -f software.lock.json ]] || exit 9\n')
        for name in ['forward_cli.sh','source_sync.py']:
            source=ROOT/'scripts'/name
            if source.exists():(self.repo/'scripts'/name).write_bytes(source.read_bytes())
        external=self.work/'external';external.mkdir()
        orb=external/'orbctl'
        orb.write_text('''#!/usr/bin/env python3
import os,subprocess,sys
from pathlib import Path
args=sys.argv[1:]
if args[0]=='info':sys.exit(0)
if args[0]!='run':sys.exit(2)
i=1;cwd=None;user=None
while i<len(args) and args[i].startswith('-'):
 if args[i]=='-w':cwd=args[i+1]
 if args[i]=='-u':user=args[i+1]
 i+=2
command=args[i:]
ready=Path(os.environ['GUEST_HOME'])/'.python-ready'
if os.environ.get('SIMULATE_MISSING_PYTHON')=='true':
 if command==['sh','-c','command -v python3']:sys.exit(0 if ready.exists() else 1)
 if command[:1]==['python3'] and not ready.exists():sys.exit(127)
 package=command[2:] if command[:2]==['env','DEBIAN_FRONTEND=noninteractive'] else command
 if package[:1]==['apt-get']:
  if user!='root':sys.exit(70)
  if package==['apt-get','update']:sys.exit(0)
  if package==['apt-get','install','-y','--no-install-recommends','python3']:ready.write_text('installed');sys.exit(0)
  sys.exit(71)
if command==['printenv','HOME']:print(os.environ['GUEST_HOME']);sys.exit(0)
sys.exit(subprocess.run(command,cwd=cwd).returncode)
''');orb.chmod(0o755)
        self.env={**os.environ,'PATH':str(external)+':'+os.environ['PATH'],'GUEST_HOME':str(self.guest),
                  'REPO_ROOT':str(self.repo),'LINUX_ENV_NAME':'fixture','LINUX_USER':'fixture',
                  'LINUX_NORMAL_PASSWD':'','LINUX_ROOT_PASSWD':'','OPERATOR':'install','OPTIONAL':'false',
                  'CONCURRENT':'1','TIMEOUT':'10','SKIP_SYSTEM':'true'}

    def wrapper(self):
        return subprocess.run(['bash','-c','ENABLE_APPS=(); DISABLE_APPS=(); ONLY_APPS=(); APP_FLAG_ARGS=(); source "$1"',
                               'bash',str(ROOT/'scripts/setup_linux_vm.sh')],env=self.env,capture_output=True,text=True,timeout=10)

    def archive(self,files):
        data=io.BytesIO()
        with tarfile.open(fileobj=data,mode='w:gz') as out:
            for name,content in files.items():
                entry=tarfile.TarInfo(name);payload=content.encode();entry.size=len(payload)
                out.addfile(entry,io.BytesIO(payload))
        return data.getvalue()

    def sync(self,files,destination=None):
        return subprocess.run(['python3',str(ROOT/'scripts/source_sync.py'),str(destination or self.work/'deployment')],
                              input=self.archive({'software.lock.json':'{}',**files}),capture_output=True,timeout=10)

    def test_guest_without_python_is_bootstrapped_before_source_receiver(self):
        self.env['SIMULATE_MISSING_PYTHON']='true'
        result=self.wrapper();self.assertEqual(result.returncode,0,result.stderr)
        self.assertTrue((self.guest/'.python-ready').is_file())
        self.assertTrue((self.guest/'dev-env-linux/software.lock.json').is_file())

    def test_vm_wrapper_delivers_repository_lock(self):
        result=self.wrapper();self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((self.guest/'dev-env-linux/software.lock.json').read_bytes(),(self.repo/'software.lock.json').read_bytes())

    def test_vm_wrapper_refuses_overwriting_guest_edits_before_any_source_change(self):
        (self.repo/'build.sh').write_text('#!/usr/bin/env bash\nexit 0\n')
        result=self.wrapper();self.assertEqual(result.returncode,0,result.stderr)
        deployed=self.guest/'dev-env-linux'
        (deployed/'build.sh').write_text('my guest edits')
        (self.repo/'build.sh').write_text('different upstream version')
        (self.repo/'config/new').write_text('new source')
        result=self.wrapper();self.assertNotEqual(result.returncode,0)
        self.assertEqual((deployed/'build.sh').read_text(),'my guest edits')
        self.assertFalse((deployed/'config/new').exists())

    def test_repeat_sync_updates_owned_files_but_preserves_extra_notes(self):
        files={'build.sh':'one','software.lock.json':'{"version":1}','config/old':'old'}
        result=self.sync(files);self.assertEqual(result.returncode,0,result.stderr)
        root=self.work/'deployment';(root/'notes').write_text('my notes')
        result=self.sync({'build.sh':'two','software.lock.json':'{"version":2}'})
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((root/'build.sh').read_text(),'two');self.assertFalse((root/'config/old').exists())
        self.assertEqual((root/'notes').read_text(),'my notes')

    def test_unknown_existing_source_is_not_overwritten(self):
        root=self.work/'deployment';root.mkdir();(root/'build.sh').write_text('my project')
        result=self.sync({'build.sh':'incoming'})
        self.assertNotEqual(result.returncode,0);self.assertEqual((root/'build.sh').read_text(),'my project')

    def test_modified_removed_file_blocks_entire_sync(self):
        self.assertEqual(self.sync({'build.sh':'one','config/old':'old'}).returncode,0)
        root=self.work/'deployment';(root/'config/old').write_text('my edit')
        result=self.sync({'build.sh':'two'})
        self.assertNotEqual(result.returncode,0);self.assertEqual((root/'build.sh').read_text(),'one')
        self.assertEqual((root/'config/old').read_text(),'my edit')

    def test_parent_symlink_does_not_write_outside_deployment(self):
        root=self.work/'deployment';root.mkdir();outside=self.work/'outside';outside.mkdir()
        (root/'config').symlink_to(outside)
        result=self.sync({'config/new':'incoming'})
        self.assertNotEqual(result.returncode,0);self.assertFalse((outside/'new').exists())

    def test_archive_traversal_is_rejected_before_creating_destination(self):
        result=self.sync({'../escape':'bad','build.sh':'new'})
        self.assertNotEqual(result.returncode,0)
        self.assertFalse((self.work/'escape').exists());self.assertFalse((self.work/'deployment').exists())
