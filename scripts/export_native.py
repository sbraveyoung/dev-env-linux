#!/usr/bin/env python3
"""Generate native package inventory for a distro-specific validation record."""
import json
from pathlib import Path
import shutil
import subprocess
os_release=dict(line.split('=',1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
if shutil.which('dpkg-query'):
    output=subprocess.check_output(['dpkg-query','-W','-f=${Package}=${Version}\n'],text=True)
else:
    output=subprocess.check_output(['rpm','-qa','--qf','%{NAME}=%{VERSION}-%{RELEASE}.%{ARCH}\n'],text=True)
print(json.dumps({'distro':os_release['ID'].strip('"'),'release':os_release['VERSION_ID'].strip('"'),
                  'packages':sorted(output.splitlines())},indent=2))
