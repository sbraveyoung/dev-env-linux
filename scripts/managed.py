#!/usr/bin/env python3
"""Private versioned installations. Registry integrity is enforced by each package client."""
import json
import fcntl
import os
from pathlib import Path
import re
import shutil
import shlex
import time
import subprocess
import sys
import urllib.request

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.catalog import managed_apps

CATALOG=managed_apps()
BASE = Path(os.environ.get('APP_PATH', str(Path.home()/'.local/share/dev-env-linux/app'))) / 'managed'
BIN = Path(os.environ.get('BIN_PATH', str(Path.home()/'.local/bin')))


def run(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, **kwargs)


def api(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.load(response)
        except OSError:
            if attempt==2: raise
            time.sleep(attempt+1)


def version(spec):
    package, backend = spec['package'], spec['backend']
    if backend == 'pip':
        return api('https://pypi.org/pypi/'+package+'/json')['info']['version']
    if backend == 'npm':
        return api('https://registry.npmjs.org/'+package.replace('/', '%2f'))['dist-tags']['latest']
    if backend == 'cargo':
        request = urllib.request.Request('https://crates.io/api/v1/crates/'+package,
                                         headers={'User-Agent':'dev-env-linux installer'})
        return api(request)['crate']['max_stable_version']
    if backend in {'git','source'}:
        refs=['refs/tags/'+spec['ref'],'refs/tags/'+spec['ref']+'^{}'] if spec.get('ref') else ['HEAD']
        output=run('git','-c','http.version=HTTP/1.1','ls-remote',package,*refs,capture_output=True,timeout=60).stdout
        commits=dict(line.split() for line in output.splitlines())
        release=next((sha for sha,ref in commits.items() if ref.endswith('^{}')),next(iter(commits),None))
        if not release or not re.fullmatch('[0-9a-f]{40}',release):raise RuntimeError('source reference could not be resolved')
        return release
    # Resolve the actual command module, including tools nested under cmd/.
    env = {**os.environ, 'GOTOOLCHAIN':'auto'}
    return json.loads(run('go','list','-m','-json',package.split('/cmd/')[0]+'@latest',
                         capture_output=True,env=env).stdout)['Version']


def atomic_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,indent=2)+'\n')
    temp.replace(path)


def activate(app, destination, record):
    BIN.mkdir(parents=True,exist_ok=True)
    for name, relative in record['commands'].items():
        if Path(name).name!=name or name in {'.','..'}:
            raise RuntimeError('invalid command name: '+name)
        link = BIN/name
        target = destination/relative
        if not target.exists():
            raise RuntimeError('missing installed command: '+str(target))
        if link.exists() or link.is_symlink():
            if not link.is_symlink() or not str(link.readlink()).startswith(str(BASE)+'/'):
                raise RuntimeError('refusing to overwrite unmanaged file: '+str(link))
    for name, relative in record['commands'].items():
        link = BIN/name
        target = destination/relative
        temp = BIN/('.'+name+'.dev-env-link')
        temp.unlink(missing_ok=True)
        temp.symlink_to(target)
        temp.replace(link)
    if record['backend'] == 'git':
        source_link = app/'source'
        source_link.unlink(missing_ok=True)
        source_link.symlink_to(destination/'source')
    current_file=app/'current.json'
    old=json.loads(current_file.read_text()) if current_file.exists() else {}
    for name in set(old.get('commands',{}))-set(record['commands']):
        link=BIN/name
        if link.is_symlink() and str(link.readlink()).startswith(str(app)+'/'): link.unlink()
    atomic_json(current_file,record)


def describe(spec,destination,release):
    backend,package=spec['backend'],spec['package']
    commands = spec.get('commands')
    if commands is not None:
        commands = {name:'source/'+relative for name,relative in commands.items()}
    elif backend == 'npm':
        metadata=json.loads((destination/'node_modules'/package/'package.json').read_text())
        names=metadata.get('bin',{})
        if isinstance(names,str): names={package.rsplit('/',1)[-1]:names}
        commands={name.rsplit('/',1)[-1]:'node_modules/.bin/'+name.rsplit('/',1)[-1] for name in names}
        if package=='@squoosh/cli': commands={'squoosh-cli':commands['squoosh-cli']}
    elif backend == 'pip':
        script='import importlib.metadata as m,json,sys; print(json.dumps([e.name for e in m.distribution(sys.argv[1]).entry_points if e.group=="console_scripts"]))'
        names=json.loads(run(str(destination/'bin/python'),'-c',script,package,capture_output=True).stdout)
        names+=spec.get('bin_scripts',[])
        commands={name:'bin/'+name for name in names}
    else:
        excluded = {'python','python3','python3.12','activate','activate.csh','activate.fish','Activate.ps1','pip','pip3','pip3.12'}
        commands = {p.name:str(p.relative_to(destination)) for p in (destination/'bin').glob('*')
                    if p.name not in excluded and os.access(p,os.X_OK) and not p.name.startswith('python') and not p.name.startswith('pip')}
    if package=='@squoosh/cli':
        compat=destination/'squoosh-compat.cjs'
        shutil.copy2(Path(__file__).parents[1]/'config/squoosh-compat.cjs',compat)
        launcher=destination/'bin/squoosh-cli'
        launcher.parent.mkdir(exist_ok=True)
        cli=destination/'node_modules/.bin/squoosh-cli'
        launcher.write_text('#!/bin/sh\nexec node --require '+shlex.quote(str(compat))+' '+shlex.quote(str(cli))+' "$@"\n')
        launcher.chmod(0o755)
        commands['squoosh-cli']='bin/squoosh-cli'
    for alias,original in spec.get('aliases',{}).items():
        commands[alias]=commands[original]
    record = {**spec,'version':release,'commands':commands}
    if backend == 'pip':
        record['dependencies'] = run(str(destination/'bin/python'),'-m','pip','freeze',capture_output=True).stdout.splitlines()
    elif backend == 'go':
        record['verification'] = 'Go module checksum database'
    elif backend == 'npm':
        record['npm_strategy'] = 'nested'
        record['dependency_lock'] = json.loads((destination/'package-lock.json').read_text())
    elif backend == 'cargo':
        record['verification'] = 'Cargo.lock and registry crate checksums'
    record['schema']=4
    return record


def _operate(name, operator):
    if name not in CATALOG:
        raise RuntimeError('unknown managed software: '+name)
    spec = CATALOG[name]
    app = BASE/name
    app.mkdir(parents=True,exist_ok=True)
    current = json.loads((app/'current.json').read_text()) if (app/'current.json').exists() else None
    if operator == 'uninstall':
        if current:
            for command in current['commands']:
                link = BIN/command
                if link.is_symlink() and str(link.readlink()).startswith(str(app)+'/'):
                    link.unlink()
            (app/'current.json').unlink()
            (app/'source').unlink(missing_ok=True)
        return  # Retain versions for explicit rollback; never delete user directories.
    if operator == 'rollback':
        previous = json.loads((app/'previous.json').read_text())
        activate(app,app/previous['version'],previous)
        atomic_json(app/'lock.json',previous)
        if current: atomic_json(app/'previous.json',current)
        return
    locked = app/'lock.json'
    if spec.get('version'):
        release=spec['version']
    elif operator == 'install' and locked.exists():
        release = json.loads(locked.read_text())['version']
    elif operator == 'install' and (repository_lock := Path(__file__).parents[1]/'software.lock.json').exists() and name in json.loads(repository_lock.read_text()):
        release = json.loads(repository_lock.read_text())[name]['version']
    else:
        release = version(spec)
    if not re.fullmatch(r'[a-zA-Z0-9._+-]+',release):
        raise RuntimeError('invalid registry version')
    destination = app/release
    receipt = destination/'receipt.json'
    if receipt.exists() and spec['backend']=='npm' and json.loads(receipt.read_text()).get('npm_strategy')!='nested':
        # All these files belong to this private, versioned installation.
        shutil.rmtree(destination/'node_modules',ignore_errors=True)
        (destination/'package-lock.json').unlink(missing_ok=True)
        receipt.unlink()
    if not receipt.exists():
        destination.mkdir(parents=True,exist_ok=True)
        backend,package = spec['backend'],spec['package']
        repo_lock=Path(__file__).parents[1]/'software.lock.json'
        resolved=json.loads(repo_lock.read_text()).get(name,{}) if repo_lock.exists() else {}
        if resolved.get('version') != release: resolved={}
        if backend == 'go':
            env = {**os.environ,'GOMAXPROCS':os.environ.get('GOMAXPROCS','2'),'GOBIN':str(destination/'bin'),'GOTOOLCHAIN':'auto','GOSUMDB':'sum.golang.org'}
            run('go','install',package+'@'+release,env=env)
        elif backend == 'cargo':
            cargo_env={**os.environ}
            for key,value in spec.get('cargo_profile',{}).items():cargo_env['CARGO_PROFILE_RELEASE_'+key.upper()]=str(value)
            run(shutil.which('cargo') or str(Path.home()/'.cargo/bin/cargo'),'install','--locked','--version',release,
                '--root',str(destination),'--jobs',os.environ.get('CARGO_BUILD_JOBS','2'),package,env=cargo_env)
        elif backend == 'npm':
            if isinstance(resolved.get('dependency_lock'),dict):
                atomic_json(destination/'package-lock.json',resolved['dependency_lock'])
                dependencies=resolved['dependency_lock']['packages']['']['dependencies']
                atomic_json(destination/'package.json',{'dependencies':dependencies})
                run('npm','ci','--install-strategy=nested','--prefix',str(destination))
            else:
                run('npm','install','--install-strategy=nested','--prefix',str(destination),package+'@'+release)
        elif backend == 'pip':
            run('python3','-m','venv',str(destination))
            args=[]
            if resolved.get('dependencies'):
                constraints=destination/'constraints.txt'
                constraints.write_text('\n'.join(resolved['dependencies'])+'\n')
                args=['--constraint',str(constraints)]
            run(str(destination/'bin/python'),'-m','pip','install',*args,package+'=='+release)
        elif backend in {'git','source'}:
            source = destination/'source'
            if not (source/'.git').exists():
                run('git','init',str(source))
                run('git','-C',str(source),'remote','add','origin',package)
            present=subprocess.run(['git','-C',str(source),'cat-file','-e',release+'^{commit}'],capture_output=True).returncode==0
            if not present:
                for attempt in range(3):
                    try:
                        run('git','-c','http.version=HTTP/1.1','-C',str(source),'fetch','--depth=1','origin',release,timeout=180)
                        break
                    except (subprocess.CalledProcessError,subprocess.TimeoutExpired):
                        if attempt==2: raise
                        time.sleep(attempt+1)
            run('git','-C',str(source),'checkout','--detach',release)
            if backend == 'source':
                if not (source/'configure').exists(): run('autoreconf','-fi',cwd=source)
                run('./configure','--prefix='+str(destination),cwd=source)
                run('make','-j2',cwd=source)
                run('make','install',cwd=source)
        atomic_json(receipt,describe(spec,destination,release))
    record = json.loads(receipt.read_text())
    if any(record.get(key)!=spec.get(key) for key in ['backend','package']):
        raise RuntimeError('recorded source differs from catalog; use upgrade with a new version or a separate APP_PATH')
    if record.get('schema',0)<4 or record.get('bin_scripts')!=spec.get('bin_scripts'):
        record=describe(spec,destination,release)
        atomic_json(receipt,record)
    if current and current['version'] != release:
        atomic_json(app/'previous.json',current)
    activate(app,destination,record)
    atomic_json(locked,record)
    print(name+': '+operator+' '+release,flush=True)


def operate(name, operator):
    if operator not in {'install','upgrade','uninstall','rollback'}:
        raise RuntimeError('unsupported operation: '+operator)
    if name not in CATALOG:
        raise RuntimeError('unknown managed software: '+name)
    app = BASE/name
    app.mkdir(parents=True,exist_ok=True)
    with (app/'.transaction.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        _operate(name,operator)


if __name__ == '__main__':
    if sys.platform != 'linux':
        raise SystemExit('Run managed installs inside an isolated Linux VM/container')
    try:
        operate(sys.argv[1],sys.argv[2])
    except (OSError,ValueError,RuntimeError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:
        print(str(error),file=sys.stderr)
        sys.exit(1)
