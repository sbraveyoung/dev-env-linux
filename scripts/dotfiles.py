#!/usr/bin/env python3
"""Apply repo dotfiles with a restorable snapshot, preserving later user edits."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import shutil
import sys
import tempfile
import uuid

ROOT=Path(__file__).resolve().parents[1]
HOME=Path.home()
STATE=Path(os.environ.get('APP_PATH',str(HOME/'.local/share/dev-env-linux/app')))/'dotfiles'
FILES={'.gitconfig':'config/.gitconfig','.ssh/relay.sh':'config/relay.sh','.ssh/login':'config/login',
       '.ssh/config':'config/.ssh_config','.config/nvim':'config/nvim','.tigrc':'config/.tigrc','.tmux.conf':'config/.tmux.conf'}

def fingerprint(path):
    if path.is_symlink(): return 'link:'+os.readlink(path)
    if path.is_dir():
        return hashlib.sha256(json.dumps([(str(p.relative_to(path)),fingerprint(p))
            for p in sorted(path.rglob('*')) if p.is_symlink() or not p.is_dir()],sort_keys=True).encode()).hexdigest()
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

def sync_directory(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)


def atomic_json(path,value):
    if path.is_symlink():raise ValueError('refusing symlinked transaction state: '+str(path))
    fd,temporary=tempfile.mkstemp(prefix='.state-',dir=STATE)
    try:
        with os.fdopen(fd,'w') as output:
            json.dump(value,output,indent=2);output.write('\n');output.flush();os.fsync(output.fileno())
        os.replace(temporary,path);sync_directory(STATE)
    finally:
        if os.path.exists(temporary):os.unlink(temporary)


def read_json(path):
    if path.is_symlink():raise ValueError('refusing symlinked transaction state: '+str(path))
    return json.loads(path.read_text()) if path.exists() else None


def target_path(relative):
    path=PurePosixPath(relative)
    if not relative or path.is_absolute() or '..' in path.parts or str(path)!=relative:
        raise ValueError('unsafe dotfile target: '+relative)
    target=HOME/relative
    for parent in target.parents:
        if parent==HOME:break
        if parent.is_symlink():raise ValueError('refusing symlinked dotfile parent: '+str(parent))
    return target


def backup_source(record):
    path=Path(record['backup'])
    if not path.parent.resolve().is_relative_to(STATE.resolve()):raise ValueError('backup outside dotfile state')
    if not path.exists() and not path.is_symlink():raise ValueError('missing original dotfile backup: '+str(path))
    return path


def stamp(path):
    digest=fingerprint(path)
    if digest is None:return None
    result={'digest':digest,'mode':path.lstat().st_mode & 0o777}
    if path.is_dir() and not path.is_symlink():
        result['permissions']=hashlib.sha256(json.dumps([(str(p.relative_to(path)),p.lstat().st_mode & 0o777)
            for p in sorted(path.rglob('*'))]).encode()).hexdigest()
    return result


def unchanged(path,record):
    if 'installed_state' in record:return stamp(path)==record['installed_state']
    # Legacy receipts did not record permissions. Content comparison remains compatible.
    return fingerprint(path)==record['installed']


def sidecar(target,name):
    if (not isinstance(name,str) or Path(name).name!=name or
            not name.startswith('.dev-env-dotfiles-')):raise ValueError('unsafe transaction sidecar')
    return target.parent/name


def prepare(current,operation):
    """Prepare every new file and backup before replacing any live target."""
    snapshot=STATE/('snapshot-'+uuid.uuid4().hex)
    desired={};files={}
    if current:
        for relative,record in current['files'].items():
            target=target_path(relative)
            if operation=='uninstall' or relative not in FILES:
                if unchanged(target,record):
                    desired[relative]=backup_source(record) if record['existed'] else None
                else:print('preserved edited dotfile: '+relative)
    if operation!='uninstall':
        for relative,source in FILES.items():
            target=target_path(relative)
            old=current['files'].get(relative) if current else None
            if old and unchanged(target,old):
                backup=Path(old['backup']);existed=old['existed']
                if existed:backup_source(old)
            else:
                backup=snapshot/relative;existed=target.exists() or target.is_symlink()
                if existed:copy(target,backup)
            desired[relative]=ROOT/source
            files[relative]={'installed':fingerprint(ROOT/source),'installed_state':stamp(ROOT/source),
                             'backup':str(backup),'existed':existed}
    bashrc=target_path('.bashrc')
    if bashrc.is_symlink():raise ValueError('refusing to rewrite symlinked shell startup file')
    startup='source '+shlex.quote(str(ROOT/'sheath/init.sh'))
    content=bashrc.read_text() if bashrc.exists() else ''
    if operation=='uninstall':
        if bashrc.exists() and current['added_startup']:
            original=current.get('startup_record')
            if original and unchanged(bashrc,original):
                desired['.bashrc']=backup_source(original) if original['existed'] else None
            else:
                desired['.bashrc']=''.join(line for line in content.splitlines(keepends=True)
                                          if line.rstrip('\n')!=current['startup']).encode()
        receipt=None
    else:
        added=startup not in content.splitlines()
        startup_record=current.get('startup_record') if current else None
        if added:
            updated=(content+('' if not content or content.endswith('\n') else '\n')+startup+'\n').encode()
            if startup_record and unchanged(bashrc,startup_record):
                backup=Path(startup_record['backup']);existed=startup_record['existed']
                if existed:backup_source(startup_record)
            else:
                backup=snapshot/'.bashrc';existed=bashrc.exists()
                if existed:copy(bashrc,backup)
            startup_record={'installed':hashlib.sha256(updated).hexdigest(),
                            'installed_state':{'digest':hashlib.sha256(updated).hexdigest(),
                                               'mode':bashrc.stat().st_mode & 0o777 if bashrc.exists() else 0o600},
                            'backup':str(backup),'existed':existed}
            desired['.bashrc']=updated
        receipt={'files':files,'startup':startup,'added_startup':added or bool(current and current['added_startup']),
                 'startup_record':startup_record}
    actions=[];nonce=uuid.uuid4().hex
    try:
        for index,(relative,source) in enumerate(desired.items()):
            target=target_path(relative);target.parent.mkdir(parents=True,exist_ok=True)
            new_name=f'.dev-env-dotfiles-{nonce}-{index}.new'
            old_name=f'.dev-env-dotfiles-{nonce}-{index}.old'
            prepared=sidecar(target,new_name)
            action={'relative':relative,'before':stamp(target),'after':None,'prepared':new_name,'holding':old_name}
            actions.append(action)
            if isinstance(source,bytes):
                prepared.write_bytes(source)
                prepared.chmod(target.stat().st_mode & 0o777 if target.exists() else 0o600)
            elif source is not None:copy(source,prepared)
            action['after']=stamp(prepared)
            if action['before']==action['after']:
                remove(prepared);actions.pop()
        return {'schema':1,'phase':'prepared','actions':actions,'before':current,'after':receipt,'snapshot':snapshot.name}
    except BaseException:
        for action in actions:remove(sidecar(target_path(action['relative']),action['prepared']))
        if snapshot.exists():remove(snapshot)
        raise


def cleanup(journal,rollback=False):
    for action in journal['actions']:
        target=target_path(action['relative'])
        for key,expected in [('holding',action['before']),('prepared',action['after'])]:
            path=sidecar(target,action[key]);actual=stamp(path)
            if actual is not None:
                if actual!=expected:raise ValueError('preserved modified transaction file: '+str(path))
                remove(path)
        sync_directory(target.parent)
    if rollback:
        name=journal['snapshot']
        if not isinstance(name,str) or not name.startswith('snapshot-') or Path(name).name!=name:
            raise ValueError('unsafe snapshot path')
        remove(STATE/name)
    (STATE/'pending.json').unlink(missing_ok=True);sync_directory(STATE)


def recover():
    journal=read_json(STATE/'pending.json')
    if journal is None:return
    if (not isinstance(journal,dict) or journal.get('schema')!=1 or
            journal.get('phase') not in ('prepared','committing') or not isinstance(journal.get('actions'),list)):
        raise ValueError('invalid pending dotfile transaction')
    current=read_json(STATE/'current.json')
    if journal['phase']=='committing' and current==journal['after']:
        cleanup(journal);return
    if current!=journal['before']:raise ValueError('dotfile receipt changed during recovery; preserved all files')
    conflicts=[]
    for action in journal['actions']:
        target=target_path(action['relative']);holding=sidecar(target,action['holding'])
        actual=stamp(target);held=stamp(holding)
        if held is not None:
            if held!=action['before'] or actual not in (None,action['after']):conflicts.append(action['relative'])
        elif actual!=action['before'] and not (action['before'] is None and actual==action['after']):
            conflicts.append(action['relative'])
    if conflicts:raise ValueError('recovery conflicts; preserved user edits: '+', '.join(conflicts)+
                                  '; retain pending.json and sidecar files until edits are saved and conflict is resolved')
    for action in reversed(journal['actions']):
        target=target_path(action['relative']);holding=sidecar(target,action['holding'])
        if stamp(holding) is not None:
            remove(target);os.replace(holding,target)
        elif action['before'] is None:remove(target)
        sync_directory(target.parent)
    cleanup(journal,rollback=True)
    print('recovered interrupted dotfile operation')


def apply(operation):
    if operation not in ('install','upgrade','uninstall','recover'):raise ValueError('unsupported dotfile operation')
    if STATE.is_symlink():raise ValueError('refusing symlinked dotfile state')
    STATE.mkdir(parents=True,exist_ok=True)
    fd=os.open(STATE/'.transaction.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        recover()
        if operation=='recover':return
        current=read_json(STATE/'current.json')
        if operation=='install' and current is not None:
            print('dotfiles already installed; use upgrade to apply repository changes');return
        if operation=='uninstall' and current is None:return
        journal=prepare(current,operation)
        started=False
        try:
            atomic_json(STATE/'pending.json',journal)
            started=True
            for action in journal['actions']:
                target=target_path(action['relative'])
                if stamp(target)!=action['before']:raise ValueError('dotfile changed before replacement: '+str(target))
                if action['before'] is not None:os.replace(target,sidecar(target,action['holding']))
                if action['after'] is not None:os.replace(sidecar(target,action['prepared']),target)
                sync_directory(target.parent)
            journal['phase']='committing';atomic_json(STATE/'pending.json',journal)
            if journal['after'] is None:
                (STATE/'current.json').unlink();sync_directory(STATE)
            else:atomic_json(STATE/'current.json',journal['after'])
            cleanup(journal)
        except BaseException:
            if started or (STATE/'pending.json').exists():recover()
            else:cleanup(journal,rollback=True)
            raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=['install','upgrade','uninstall','recover'])
    args=parser.parse_args()
    try:apply(args.operation)
    except (OSError,ValueError,KeyError) as error:parser.exit(2,str(error)+'\n')
