#!/usr/bin/env bash
# Run inside an isolated VM/container: no installers or network access.
set -euo pipefail
[[ $(uname -s) == Linux ]] || { echo "Run checks inside an isolated Linux VM/container" >&2; exit 2; }
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"
export PYTHONDONTWRITEBYTECODE=1
python3 scripts/catalog.py validate
python3 - <<'PY'
from pathlib import Path
import os
import subprocess

files = []
for directory, subdirs, names in os.walk('.'):
    subdirs[:] = [name for name in subdirs if name not in {'.git', '.planning', '__pycache__', 'archive', '.local'}]
    files.extend(Path(directory) / name for name in names if name.endswith('.sh'))
for path in sorted(files):
    subprocess.run(['bash', '-n', str(path)], check=True)
print(f'Shell syntax: {len(files)} files passed', flush=True)
PY
python3 -m unittest discover -s tests -v
if command -v shellcheck >/dev/null 2>&1; then
  # Globals are shared by sourced modules; distro/integration source paths are dynamic.
  shellcheck -S warning -e SC2034,SC1090 build.sh scripts/*.sh scripts/distro/*.sh \
    sheath/*.sh config/relay.sh tests/orb_smoke.sh
fi
