#!/usr/bin/env python3
"""Real per-app installs in a disposable Linux VM; never run on the host."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

if sys.platform != 'linux':
    raise SystemExit('Linux isolation required')
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from scripts.catalog import load_or_exit

catalog=load_or_exit()
names=list(catalog['profiles']['linux-default'])
# Toolchains first: command modules and Rust packages depend on them.
names=[name for name in ['golang','rust'] if name in names]+[name for name in names if name not in {'golang','rust'}]
results=Path(os.environ.get('RESULTS_DIR',str(Path.home()/'dev-env-full-results')))
results.mkdir(parents=True,exist_ok=True)
report=[]
for name in names:
    start=time.monotonic()
    with (results/(name+'.log')).open('w') as log:
        result=subprocess.run(['bash',str(root/'build.sh'),'--skip-system','--only='+name,'--timeout=1800'],
                              cwd=root,stdout=log,stderr=subprocess.STDOUT,
                              env={**os.environ,'SKIP_VERSION_CHECK':'true'})
    row={'app':name,'exit':result.returncode,'seconds':round(time.monotonic()-start,1),'log':name+'.log'}
    report.append(row)
    (results/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(row),flush=True)
    if result.returncode:
        print(''.join((results/(name+'.log')).read_text().splitlines(keepends=True)[-25:]),flush=True)
print('RESULTS '+str(results),flush=True)
raise SystemExit(any(row['exit'] for row in report))
