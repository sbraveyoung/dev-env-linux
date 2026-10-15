"""Deletion safety: real directories, receipts, links and install locks."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class GCTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.work=Path(self.temp.name);self.base=self.work/'managed';self.binary=self.work/'bin';self.binary.mkdir()
        self.app=self.base/'ccat';self.app.mkdir(parents=True)
        spec=importlib.util.spec_from_file_location('managed_gc',ROOT/'scripts/managed_gc.py')
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        self.module.BASE=self.base;self.module.BIN=self.binary;self.module.REPO_LOCK=self.work/'repo-lock.json'
        self.module.CATALOG={'ccat':{'backend':'go'}}
        for version in ['v1','v2','v3','v4']:
            folder=self.app/version;folder.mkdir();(folder/'payload').write_text(version)
            (folder/'receipt.json').write_text(json.dumps({'version':version,'backend':'go','commands':{}}))
        for kind,version in [('current','v4'),('previous','v3'),('lock','v4')]:
            (self.app/(kind+'.json')).write_text(json.dumps({'version':version}))

    def test_preview_keeps_all_files_and_protects_rollback(self):
        result=self.module.collect('ccat',apply=False,keep=0)
        self.assertEqual({x['version'] for x in result['candidates']},{'v1','v2'})
        self.assertTrue((self.app/'v1').exists())
        self.assertTrue((self.app/'v3').exists())

    def test_apply_protects_repository_lock_and_external_link(self):
        self.module.REPO_LOCK.write_text(json.dumps({'ccat':{'version':'v2'}}))
        (self.binary/'other-tool').symlink_to(self.app/'v1/payload')
        result=self.module.collect('ccat',apply=True,keep=0)
        self.assertEqual(result['candidates'],[])
        self.assertTrue((self.app/'v1').exists())
        self.assertTrue((self.app/'v2').exists())

    def test_apply_removes_only_unreferenced_receipted_versions(self):
        orphan=self.app/'user-data';orphan.mkdir();(orphan/'important').write_text('keep')
        external=self.work/'outside';external.mkdir();(external/'important').write_text('keep')
        (self.app/'v0').symlink_to(external,target_is_directory=True)
        result=self.module.collect('ccat',apply=True,keep=0)
        self.assertFalse((self.app/'v1').exists())
        self.assertFalse((self.app/'v2').exists())
        self.assertTrue((self.app/'v3').exists())
        self.assertTrue((external/'important').exists())
        self.assertTrue((orphan/'important').exists())
        self.assertEqual(len(result['removed']),2)

    def test_corrupt_state_fails_closed(self):
        (self.app/'previous.json').write_text('{broken')
        with self.assertRaises(ValueError):self.module.collect('ccat',apply=True,keep=0)
        self.assertTrue((self.app/'v1').exists())

    def test_symlinked_transaction_lock_fails_closed(self):
        outside=self.work/'outside-lock';outside.write_text('keep')
        (self.app/'.transaction.lock').symlink_to(outside)
        with self.assertRaises(ValueError):self.module.collect('ccat',apply=True,keep=0)
        self.assertTrue((self.app/'v1').exists())
        self.assertEqual(outside.read_text(),'keep')
