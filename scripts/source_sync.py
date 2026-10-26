#!/usr/bin/env python3
"""Receive a source-only archive inside a guest without overwriting local edits."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tarfile
import tempfile

DIRECTORIES={'scripts','sheath','config','tests'}
FILES={'build.sh','software.lock.json'}
MANIFEST='.dev-env-source-manifest.json'


def safe_path(name):
    path=PurePosixPath(name)
    if (not name or str(path)!=name or path.is_absolute() or '..' in path.parts or
            not (path.parts[0] in DIRECTORIES or name in FILES)):
        raise ValueError('invalid source archive path: '+name)
    return path


def archive(source):
    result={}
    with tarfile.open(fileobj=source,mode='r|gz') as incoming:
        for entry in incoming:
            name=entry.name.rstrip('/') if entry.isdir() else entry.name
            safe_path(name)
            if entry.isdir():continue
            if not entry.isfile() or name in result:raise ValueError('unsupported or duplicate archive entry: '+name)
            with incoming.extractfile(entry) as content:data=content.read()
            result[name]=(data,entry.mode & 0o777)
    if not FILES.issubset(result):raise ValueError('source archive must include build.sh and software.lock.json')
    return result


def describe(data,mode):
    return {'sha256':hashlib.sha256(data).hexdigest(),'mode':mode}


def current(path):
    if path.is_symlink():raise ValueError('refusing symlinked source: '+str(path))
    if not path.exists():return None
    if not path.is_file():raise ValueError('source path is not a regular file: '+str(path))
    return describe(path.read_bytes(),stat.S_IMODE(path.stat().st_mode))


def destination(root,name):
    safe_path(name)
    path=root/name
    for parent in path.parents:
        if parent==root:break
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            raise ValueError('refusing non-directory or symlinked source parent: '+str(parent))
    return path


def atomic_write(path,data,mode=0o600):
    fd,temporary=tempfile.mkstemp(prefix='.dev-env-write-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as output:
            output.write(data);os.fchmod(output.fileno(),mode);output.flush();os.fsync(output.fileno())
        os.replace(temporary,path)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)


def sync(root,incoming):
    if root.is_symlink():raise ValueError('refusing symlinked deployment directory')
    root.mkdir(parents=True,exist_ok=True)
    fd=os.open(root/'.dev-env-source-sync.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        manifest=root/MANIFEST
        if manifest.is_symlink():raise ValueError('refusing symlinked source manifest')
        old={}
        if manifest.exists():
            state=json.loads(manifest.read_text())
            if not isinstance(state,dict) or state.get('schema')!=1 or not isinstance(state.get('files'),dict):
                raise ValueError('invalid source manifest')
            old=state['files']
            for name,record in old.items():
                safe_path(name)
                if (not isinstance(record,dict) or not isinstance(record.get('sha256'),str) or
                        not re.fullmatch(r'[0-9a-f]{64}',record['sha256']) or type(record.get('mode')) is not int or
                        not 0<=record['mode']<=0o777):raise ValueError('invalid source record: '+name)
        new={name:describe(*record) for name,record in incoming.items()}
        observed={};conflicts=[]
        # Inspect the entire delivery before changing any source file.
        for name in sorted(old.keys()|new.keys()):
            observed[name]=current(destination(root,name))
            if observed[name]!=new.get(name) and observed[name]!=old.get(name):conflicts.append(name)
        if conflicts:
            raise ValueError('guest source conflicts; no source files changed: '+', '.join(conflicts)+
                             '. Save guest edits elsewhere or select a separate VM; do not overwrite them blindly.')
        for name in sorted(observed):
            target=destination(root,name)
            if observed[name]==new.get(name):continue
            if name in incoming:
                target.parent.mkdir(parents=True,exist_ok=True)
                atomic_write(target,*incoming[name])
            else:target.unlink()
        atomic_write(manifest,(json.dumps({'schema':1,'files':new},indent=2)+'\n').encode())
        print('source delivery verified: '+str(len(new))+' files; repository lock included')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    try:sync(args.destination,archive(sys.stdin.buffer))
    except (OSError,ValueError,tarfile.TarError) as error:parser.exit(2,str(error)+'\n')
