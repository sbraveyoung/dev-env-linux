#!/usr/bin/env python3
"""Generate the repository lock from successfully installed managed receipts."""
import json
import os
import argparse
from pathlib import Path
import re
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.catalog import managed_apps

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--merge',action='append',default=[],help='fill missing apps from another verified receipt export; local records win')
args=parser.parse_args()
catalog=managed_apps()
base=Path(os.environ.get('APP_PATH',str(Path.home()/'.local/share/dev-env-linux/app')))/'managed'
records={path.parent.name:json.loads(path.read_text()) for path in sorted(base.glob('*/current.json'))}
for filename in args.merge:
    donor=json.loads(Path(filename).read_text())
    if not isinstance(donor,dict):parser.error('invalid donor export')
    for name,record in donor.items():
        spec=catalog.get(name,{})
        if not isinstance(record,dict) or not spec or any(record.get(k)!=spec.get(k) for k in ['backend','package']):
            parser.error('donor source differs from catalog: '+name)
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+-]*',record.get('version','')):
            parser.error('invalid donor version: '+name)
        records.setdefault(name,record)
records=dict(sorted(records.items()))
print(json.dumps(records,indent=2))
