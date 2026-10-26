#!/usr/bin/env python3
"""Apply repo dotfiles with a restorable snapshot, preserving later user edits."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
HOME=Path.home()
STATE=Path(os.environ.get('APP_PATH',str(HOME/'.local/share/dev-env-linux/app')))/'dotfiles'
FILES={'.gitconfig':'config/.gitconfig','.ssh/relay.sh':'config/relay.sh','.ssh/login':'config/login',
       '.ssh/config':'config/.ssh_config','.config/nvim':'config/nvim','.tigrc':'config/.tigrc','.tmux.conf':'config/.tmux.conf'}

def fingerprint(path):
    if path.is_symlink(): return 'link:'+os.readlink(path)
    if path.is_dir():
        return hashlib.sha256(json.dumps([(str(p.relative_to(path)),fingerprint(p))
            for p in sorted(path.rglob('*')) if not p.is_dir()],sort_keys=True).encode()).hexdigest()
    if path.is_file(): return hashlib.sha256(path.read_bytes()).hexdigest()
    return None

def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    if source.is_symlink():target.symlink_to(os.readlink(source))
    elif source.is_dir():shutil.copytree(source,target,symlinks=True)
    else:shutil.copy2(source,target)

def remove(path):
    if path.is_symlink() or path.is_file():path.unlink()
    elif path.is_dir():shutil.rmtree(path)

def restore(relative,record):
    target=HOME/relative
    if fingerprint(target)!=record['installed']:
        print('preserved edited dotfile: '+relative)
        return
    remove(target)
    if record['existed']:copy(Path(record['backup']),target)

def apply(operation):
    STATE.mkdir(parents=True,exist_ok=True)
    receipt=STATE/'current.json'
    current=json.loads(receipt.read_text()) if receipt.exists() else None
    if operation=='install' and current is not None:
        print('dotfiles already installed; use upgrade to apply repository changes')
        return
    if operation=='uninstall':
        if not current:return
        for relative,record in current['files'].items():
            restore(relative,record)
        bashrc=HOME/'.bashrc'
        if bashrc.exists() and current['added_startup']:
            lines=bashrc.read_text().splitlines(keepends=True)
            bashrc.write_text(''.join(line for line in lines if line.rstrip('\n')!=current['startup']))
        receipt.unlink()
        return
    snapshot=STATE/('snapshot-'+str(time.time_ns()))
    snapshot.mkdir()
    files={}
    if current:
        for relative,record in current['files'].items():
            if relative not in FILES:restore(relative,record)
    for relative,source in FILES.items():
        target=HOME/relative
        # Keep original backup across repeated upgrades; record intervening edits.
        old=current['files'].get(relative) if current else None
        if old and fingerprint(target)==old['installed']:
            backup=Path(old['backup']); existed=old['existed']
        else:
            backup=snapshot/relative;existed=target.exists() or target.is_symlink()
            if existed:copy(target,backup)
        remove(target);copy(ROOT/source,target)
        files[relative]={'installed':fingerprint(target),'backup':str(backup),'existed':existed}
    bashrc=HOME/'.bashrc'
    startup='source '+shlex.quote(str(ROOT/'sheath/init.sh'))
    lines=bashrc.read_text().splitlines() if bashrc.exists() else []
    added=startup not in lines
    if added:
        with bashrc.open('a') as output:output.write('\n'+startup+'\n')
    if current:added=added or current['added_startup']
    receipt.write_text(json.dumps({'files':files,'startup':startup,'added_startup':added},indent=2)+'\n')

if __name__=='__main__':apply(sys.argv[1])
