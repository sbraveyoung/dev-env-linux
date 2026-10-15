"""Failed child exec must not unwind and remove the parent's fixture directory."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest

@unittest.skipUnless(sys.platform=='linux','PTY tests require isolated Linux')
class PtyRunnerTests(unittest.TestCase):
    def test_missing_command_preserves_parent_fixture(self):
        spec=importlib.util.spec_from_file_location('tui_smoke',Path(__file__).with_name('tui_smoke.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            fixture=Path(directory);(fixture/'sentinel').write_text('keep')
            row,data=module.interact(['dev-env-definitely-missing-command'],dict(os.environ),fixture,[],b'ready',timeout=2)
            self.assertEqual(row['exit'],127)
            self.assertFalse(row['timeout'])
            self.assertEqual((fixture/'sentinel').read_text(),'keep')
