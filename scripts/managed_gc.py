#!/usr/bin/env python3
"""Remove only unreferenced, receipted versions under installer transaction locks."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import sys

BASE=Path(os.environ.get('APP_PATH',str(Path.home()/'.local/share/dev-env-linux/app')))/'managed'
BIN=Path(os.environ.get('BIN_PATH',str(Path.home()/'.local/bin')))
REPO_LOCK=Path(__file__).parents[1]/'software.lock.json'
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.catalog import managed_apps

CATALOG=managed_apps()


def valid_version(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+-]*',value):
        raise ValueError('invalid protected version')
    return value


def read(path):
    if path.is_symlink(): raise ValueError('refusing symlinked state: '+str(path))
    value=json.loads(path.read_text())
    if not isinstance(value,dict): raise ValueError('invalid state: '+str(path))
    return value


def size(path):
    total=0
    for directory,_,files in os.walk(path,followlinks=False):
        for name in files: total+=(Path(directory)/name).lstat().st_size
    return total


def collect(name,apply=False,keep=1):
    if name not in CATALOG or keep<0: raise ValueError('unknown app or invalid keep count')
    app=BASE/name
    result={'app':name,'apply':apply,'protected':{},'candidates':[],'removed':[]}
    if not app.exists(): return result
    if app.is_symlink() or app.resolve().parent!=BASE.resolve(): raise ValueError('unsafe managed directory')
    if (app/'.transaction.lock').is_symlink():raise ValueError('symlinked transaction lock')
    with (app/'.transaction.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        protected={}
        for kind in ['current','previous','lock']:
            state=app/(kind+'.json')
            if state.exists() or state.is_symlink():
                version=valid_version(read(state)['version'])
                protected.setdefault(version,[]).append(kind)
        if REPO_LOCK.exists() or REPO_LOCK.is_symlink():
            pinned=read(REPO_LOCK).get(name)
            if pinned:
                version=valid_version(pinned['version'])
                protected.setdefault(version,[]).append('repository lock')
        if BIN.exists():
            for link in BIN.iterdir():
                if link.is_symlink():
                    target=link.resolve()
                    if target.is_relative_to(app.resolve()):
                        version=target.relative_to(app.resolve()).parts[0]
                        protected.setdefault(version,[]).append('binary link '+link.name)
        versions=[]
        for folder in app.iterdir():
            if folder.is_symlink() or not folder.is_dir(): continue
            receipt=folder/'receipt.json'
            if not receipt.exists(): continue
            record=read(receipt)
            if record.get('version')!=folder.name or record.get('backend')!=CATALOG[name]['backend']:
                raise ValueError('invalid installation receipt: '+str(receipt))
            valid_version(folder.name)
            versions.append(folder)
        spare=sorted((v for v in versions if v.name not in protected),key=lambda p:p.stat().st_mtime_ns,reverse=True)
        for folder in spare[:keep]: protected.setdefault(folder.name,[]).append('additional retained version')
        result['protected']=protected
        for folder in spare[keep:]:
            row={'version':folder.name,'path':str(folder),'bytes':size(folder)}
            result['candidates'].append(row)
            if apply:
                # No untrusted absolute paths or symlink traversal; recheck just before deletion.
                if folder.is_symlink() or folder.resolve().parent!=app.resolve(): raise ValueError('unsafe cleanup target')
                shutil.rmtree(folder)
                result['removed'].append(row)
    return result


def main():
    if sys.platform!='linux': raise SystemExit('Run cleanup inside an isolated Linux VM/container')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only',help='comma-separated app names; default: installed catalog apps')
    parser.add_argument('--keep',type=int,default=1,help='additional unreferenced versions to retain')
    parser.add_argument('--apply',action='store_true',help='perform deletion; default is preview only')
    args=parser.parse_args()
    names=args.only.split(',') if args.only else sorted(CATALOG)
    if args.keep<0 or any(name not in CATALOG for name in names): parser.error('invalid app or keep count')
    try: print(json.dumps([collect(name,args.apply,args.keep) for name in names],indent=2))
    except (OSError,ValueError,KeyError,RuntimeError) as error: parser.exit(1,str(error)+'\n')

if __name__=='__main__':main()
