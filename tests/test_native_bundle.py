import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        spec=importlib.util.spec_from_file_location('native_bundle',ROOT/'scripts/native_bundle.py')
        self.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.module)
        (self.folder/'archives').mkdir();self.asset=self.folder/'archives/tree.deb';self.asset.write_bytes(b'package')
        self.record={'schema':1,'backend':'apt','platform':self.module.platform_id(),'roots':['tree=1.0'],
                     'assets':[{'file':'archives/tree.deb','sha256':hashlib.sha256(b'package').hexdigest()}]}
        self.save()
    def save(self):(self.folder/'manifest.json').write_text(json.dumps(self.record))
    def test_corrupt_package_rejected(self):
        self.asset.write_bytes(b'changed')
        with self.assertRaises(ValueError):self.module.verify(self.folder)
    def test_escaping_file_rejected(self):
        self.record['assets'][0]['file']='../outside.deb';self.save()
        with self.assertRaises(ValueError):self.module.verify(self.folder)
    def test_symlinked_asset_rejected(self):
        outside=self.folder/'outside';outside.write_bytes(b'package')
        self.asset.unlink();self.asset.symlink_to(outside)
        with self.assertRaises(ValueError):self.module.verify(self.folder)
    def test_different_platform_rejected(self):
        self.record['platform']={'id':'other','version':'0','arch':'amd64'};self.save()
        with self.assertRaises(ValueError):self.module.verify(self.folder)
    def test_valid_exact_version_bundle_accepted(self):
        manifest=self.module.verify(self.folder)
        self.assertEqual(manifest['roots'],['tree=1.0'])

    def test_empty_or_option_like_root_is_rejected(self):
        for roots in [[],['--allowerasing']]:
            with self.subTest(roots=roots):
                self.record['roots']=roots;self.save()
                with self.assertRaises(ValueError):self.module.verify(self.folder)
