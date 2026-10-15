#!/usr/bin/env python3
"""Build pinned Qt macOS apps and activate only installer-owned application links."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.catalog import load_or_exit, ROOT


def run(*args,**kwargs):
    return subprocess.run([str(arg) for arg in args],check=True,text=True,**kwargs)


def write_record(path,value):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)


def owned(link,app):
    return link.is_symlink() and link.resolve().is_relative_to(app.resolve())


def read_record(path,app):
    if path.is_symlink():raise ValueError('refusing symlinked application state')
    record=json.loads(path.read_text())
    target=Path(record['target'])
    if not target.resolve().is_relative_to(app.resolve()) or not target.is_dir():raise ValueError('invalid application receipt')
    return record


def activate(link,record,app):
    if (link.exists() or link.is_symlink()) and not owned(link,app):raise ValueError('refusing unmanaged application: '+str(link))
    target=Path(record['target'])
    if not target.is_dir() or not target.resolve().is_relative_to(app.resolve()):raise ValueError('invalid application target')
    link.parent.mkdir(parents=True,exist_ok=True)
    temporary=link.with_name('.'+link.name+'.dev-env-link')
    if temporary.exists() or temporary.is_symlink():raise ValueError('activation already pending: '+str(temporary))
    temporary.symlink_to(target);temporary.replace(link)


def build(spec,stage):
    dependencies=spec['brew_dependencies']
    if dependencies:run('brew','install',*dependencies)
    qt=Path(run('brew','--prefix',spec['qt_package'],capture_output=True).stdout.strip())/'bin'
    source=stage/'source';source.mkdir()
    run('git','init',source)
    run('git','fetch','--depth=1',spec['source_url'],spec['revision'],cwd=source)
    run('git','checkout','--detach','FETCH_HEAD',cwd=source)
    revision=run('git','rev-parse','HEAD',cwd=source,capture_output=True).stdout.strip()
    if revision!=spec['revision']:raise ValueError('source revision differs from declaration')
    for patch in spec.get('patches',[]):run('git','apply',ROOT/'config/patches'/patch,cwd=source)
    includes=[];libraries=[]
    if subdir:=spec.get('library_subdir'):
        library=stage/'dependencies'
        # Regenerate the bundled 2012 config.guess from configure.ac for ARM64.
        run('autoreconf','-fi',cwd=source/subdir)
        run('./configure','--prefix='+str(library),'--disable-shared',cwd=source/subdir)
        run('make','-j2',cwd=source/subdir);run('make','install',cwd=source/subdir)
        includes.append(str(library/'include'));libraries.extend(['-L'+str(library/'lib'),'-lh264bitstream'])
    for package in spec.get('link_packages',[]):
        prefix=Path(run('brew','--prefix',package,capture_output=True).stdout.strip())
        includes.append(str(prefix/'include'));libraries.extend(['-L'+str(prefix/'lib'),'-l'+package])
    arguments=[]
    if includes:arguments.append('INCLUDEPATH+='+' '.join(includes))
    if libraries:arguments.append('LIBS='+' '.join(libraries))
    run(qt/'qmake',spec['project'],'CONFIG+=release',*arguments,cwd=source)
    run('make','-j2',cwd=source)
    bundle=source/spec['bundle']
    with (bundle/'Contents/Info.plist').open('rb') as handle:info=plistlib.load(handle)
    executable=bundle/'Contents/MacOS'/info['CFBundleExecutable']
    if not executable.is_file() or not executable.resolve().is_relative_to(bundle.resolve()):raise ValueError('missing application executable')
    run(qt/'macdeployqt',bundle,'-always-overwrite')


def operate(name,operation,data):
    spec=data['apps'][name]['darwin']
    if spec.get('installer')!='qt':raise ValueError('not a Qt application: '+name)
    base=Path(os.environ.get('APP_PATH',str(Path.home()/'.local/share/dev-env-linux/app')))/'macos'
    app=base/name
    applications=Path(os.environ.get('DEV_ENV_APPLICATIONS_DIR',str(Path.home()/'Applications')))
    link=applications/Path(spec['bundle']).name
    if app.is_symlink():raise ValueError('refusing symlinked app state')
    if (link.exists() or link.is_symlink()) and not owned(link,app):raise ValueError('refusing unmanaged application: '+str(link))
    app.mkdir(parents=True,exist_ok=True)
    lock=app/'.transaction.lock'
    if lock.is_symlink():raise ValueError('refusing symlinked transaction lock')
    with lock.open('a') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX)
        current_path=app/'current.json';previous_path=app/'previous.json'
        current=read_record(current_path,app) if current_path.exists() or current_path.is_symlink() else None
        if operation=='uninstall':
            if owned(link,app):link.unlink()
            return
        if operation=='rollback':
            previous=read_record(previous_path,app)
            activate(link,previous,app)
            if current:write_record(previous_path,current)
            write_record(current_path,previous);return
        digest=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()[:12]
        destination=app/(spec['revision']+'-'+digest)
        if destination.is_symlink():raise ValueError('refusing symlinked app version')
        if not destination.exists():
            # A failed source build remains invisible; only complete deployments publish.
            with tempfile.TemporaryDirectory(prefix='.build-',dir=app) as directory:
                stage=Path(directory)
                build(spec,stage)
                stage.rename(destination)
        record={'target':str(destination/'source'/spec['bundle']),'revision':spec['revision'],'manifest':digest}
        activate(link,record,app)
        if current and current!=record:write_record(previous_path,current)
        write_record(current_path,record)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('application');parser.add_argument('operation',choices=['install','upgrade','uninstall','rollback'])
    args=parser.parse_args();data=load_or_exit()
    try:operate(args.application,args.operation,data)
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:parser.exit(1,str(error)+'\n')
