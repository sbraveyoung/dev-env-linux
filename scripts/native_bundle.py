#!/usr/bin/env python3
"""Save verified native packages with dependency closure, and restore offline."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys


def run(*args,**kwargs):return subprocess.run(args,check=True,text=True,**kwargs)
def output(*args):return run(*args,capture_output=True).stdout.strip()
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def platform_id():
    values=dict(line.split('=',1) for line in Path('/etc/os-release').read_text().splitlines() if '=' in line)
    return {'id':values['ID'].strip('"'),'version':values['VERSION_ID'].strip('"'),'arch':platform.machine()}


def verify(folder):
    folder=Path(folder)
    if (folder/'manifest.json').is_symlink():raise ValueError('symlinked manifest')
    manifest=json.loads((folder/'manifest.json').read_text())
    if manifest.get('schema')!=1 or manifest.get('backend') not in {'apt','dnf'}:raise ValueError('invalid bundle format')
    if manifest.get('platform')!=platform_id():raise ValueError('bundle platform mismatch')
    roots=manifest.get('roots')
    if not isinstance(roots,list) or not roots or any(not isinstance(root,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9+_.:~=^-]*',root) for root in roots):
        raise ValueError('invalid bundle root packages')
    if not manifest.get('assets'):raise ValueError('empty bundle')
    seen=set()
    for asset in manifest['assets']:
        relative=Path(asset['file'])
        if relative.is_absolute() or '..' in relative.parts or str(relative) in seen:raise ValueError('unsafe asset path')
        seen.add(str(relative));path=folder/relative
        if any((folder/Path(*relative.parts[:i])).is_symlink() for i in range(1,len(relative.parts)+1)):
            raise ValueError('symlinked asset')
        if not path.is_file() or digest(path)!=asset['sha256']:raise ValueError('bundle SHA256 mismatch: '+asset['file'])
    return manifest


def create(folder,packages):
    folder=Path(folder).resolve()
    if folder.exists() and any(folder.iterdir()):raise ValueError('bundle destination must be empty')
    if not packages or any(not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9+_.:-]*',p) for p in packages):raise ValueError('invalid package name')
    archives=folder/'archives';archives.mkdir(parents=True,exist_ok=True)
    backend='apt' if shutil.which('apt-get') else 'dnf'
    roots=[]
    if backend=='apt':
        for package in packages:roots.append(package+'='+output('dpkg-query','-W','-f=${Version}',package))
        (archives/'partial').mkdir();status=folder/'empty-status';status.touch()
        run('sudo','env','DEBIAN_FRONTEND=noninteractive','apt-get','-y','--download-only','--no-install-recommends',
            '-o','Dir::State::status='+str(status),'-o','Dir::Cache::archives='+str(archives),
            'install',*roots)
        assets=[]
        for path in sorted(archives.glob('*.deb')):
            fields=output('dpkg-deb','-f',str(path),'Package','Version','Architecture').splitlines()
            info=dict(line.split(': ',1) for line in fields)
            metadata=output('apt-cache','show',info['Package']+'='+info['Version'])
            records=[dict(line.split(': ',1) for line in paragraph.splitlines() if ': ' in line and not line.startswith(' '))
                     for paragraph in metadata.split('\n\n')]
            actual=digest(path)
            if not any(r.get('SHA256')==actual and r.get('Architecture')==info['Architecture'] for r in records):
                raise ValueError('package not matched to signed APT index: '+path.name)
            assets.append({'file':'archives/'+path.name,'sha256':actual,'package':info['Package'],
                           'version':info['Version'],'verification':'signed APT index SHA256'})
    else:
        for package in packages:roots.append(output('rpm','-q','--qf','%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}',package))
        run('dnf','download','--resolve','--alldeps','--destdir='+str(archives),*roots)
        assets=[]
        for path in sorted(archives.glob('*.rpm')):
            run('rpmkeys','--checksig',str(path))
            info=output('rpm','-qp','--qf','%{NAME}\n%{VERSION}-%{RELEASE}.%{ARCH}',str(path)).splitlines()
            assets.append({'file':'archives/'+path.name,'sha256':digest(path),'package':info[0],
                           'version':info[1],'verification':'RPM vendor signature'})
        if not shutil.which('createrepo_c'):raise ValueError('DNF bundle creation requires createrepo_c')
        run('createrepo_c',str(archives))
        for path in sorted((archives/'repodata').iterdir()):
            assets.append({'file':str(path.relative_to(folder)),'sha256':digest(path),'verification':'local dependency catalog; RPM assets vendor-signed'})
        keys=folder/'RPM-GPG-KEYS'
        keys.write_text(output('rpm','-q','gpg-pubkey','--qf','%{DESCRIPTION}\n')+'\n')
        assets.append({'file':keys.name,'sha256':digest(keys),'verification':'public keys from donor RPM database'})
    manifest={'schema':1,'backend':backend,'platform':platform_id(),'roots':roots,'assets':assets}
    if not assets:raise ValueError('no packages downloaded')
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return verify(folder)


def restore(folder,apply=False):
    folder=Path(folder).resolve();manifest=verify(folder)
    files=[str(folder/a['file']) for a in manifest['assets'] if a['file'].endswith(('.deb','.rpm'))]
    if not files:raise ValueError('no package assets')
    if not apply:return {'apply':False,'platform':manifest['platform'],'roots':manifest['roots'],'packages':len(files)}
    if manifest['backend']=='apt':
        run('sudo','env','DEBIAN_FRONTEND=noninteractive','dpkg','--unpack',*files)
        run('sudo','env','DEBIAN_FRONTEND=noninteractive','dpkg','--configure','--pending')
    else:
        # The caller must trust the bundle's donor; checksums detect corruption,
        # not an attacker replacing both the manifest and the public keys.
        keys=folder/'RPM-GPG-KEYS'
        if not any(a['file']==keys.name for a in manifest['assets']):raise ValueError('missing checksummed key asset')
        run('sudo','rpmkeys','--import',str(keys))
        if not (folder/'archives/repodata/repomd.xml').is_file():raise ValueError('missing offline dependency catalog; recreate bundle')
        run('sudo','dnf','--disablerepo=*','--repofrompath=offline,'+(folder/'archives').as_uri(),
            '--setopt=offline.gpgcheck=1','--setopt=offline.repo_gpgcheck=0',
            '--setopt=install_weak_deps=False','-y','install',*manifest['roots'])
    for root in manifest['roots']:
        if manifest['backend']=='apt':
            package,expected=root.split('=',1)
            if output('dpkg-query','-W','-f=${Version}',package)!=expected:raise ValueError('restored version differs: '+root)
        else:
            if output('rpm','-q','--qf','%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}',root)!=root:raise ValueError('restored version differs: '+root)
    return {'apply':True,'roots':manifest['roots'],'packages':len(files)}


def main():
    if sys.platform!='linux':raise SystemExit('Run bundles in isolated Linux, not on the host')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['create','verify','restore'])
    parser.add_argument('folder');parser.add_argument('--packages',default='jq,tree,tmux');parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    try:
        if args.operation=='create':result=create(args.folder,args.packages.split(','))
        elif args.operation=='verify':result=verify(args.folder)
        else:result=restore(args.folder,args.apply)
        print(json.dumps(result,indent=2))
    except (OSError,ValueError,KeyError,subprocess.CalledProcessError) as error:parser.exit(1,str(error)+'\n')

if __name__=='__main__':main()
