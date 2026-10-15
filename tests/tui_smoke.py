#!/usr/bin/env python3
"""Real PTY rendering/input/exit smoke tests in a disposable Linux HOME/repo."""
import argparse
import errno
import fcntl
import json
import os
from pathlib import Path
import select
import re
import signal
import struct
import subprocess
import sys
import tempfile
import termios
import time


def plain_text(data):
    return re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]|\x1b[()][0-2AB]',b'',data)


def interact(command,env,cwd,steps,ready_marker,timeout=18):
    pid,fd=os.forkpty()
    if pid==0:
        try:
            os.chdir(cwd);os.environ.clear();os.environ.update(env)
            os.execvpe(command[0],command,env)
        except BaseException as error:
            os.write(2,('TUI launch failed: '+str(error)+'\n').encode())
            os._exit(127)  # Never unwind the parent's TemporaryDirectory context.
    fcntl.ioctl(fd,termios.TIOCSWINSZ,struct.pack('HHHH',35,120,0,0))
    data=bytearray();status=None;start=time.monotonic();ready_at=None;next_step=0;timed_out=False
    try:
        while time.monotonic()-start<timeout:
            elapsed=time.monotonic()-start
            if ready_at is not None and next_step<len(steps) and elapsed-ready_at>=steps[next_step][0]:
                os.write(fd,steps[next_step][1]);next_step+=1
            ready,_,_=select.select([fd],[],[],0.05)
            if ready:
                try:chunk=os.read(fd,65536)
                except OSError as error:
                    if error.errno!=errno.EIO:raise
                    chunk=b''
                if chunk:
                    data.extend(chunk)
                    # A PTY transports bytes but does not answer terminal queries.
                    # Advertise an ordinary VT terminal without Kitty extensions.
                    if b'\x1b[?u' in chunk:os.write(fd,b'\x1b[?1;2c')
                    elif b'\x1b[c' in chunk:os.write(fd,b'\x1b[?1;2c')
                    if ready_at is None and ready_marker.lower() in plain_text(data).lower():ready_at=elapsed
            waited,code=os.waitpid(pid,os.WNOHANG)
            if waited:status=code;break
        if status is None:
            timed_out=True;os.killpg(pid,signal.SIGTERM)
            _,status=os.waitpid(pid,0)
    finally:os.close(fd)
    return {'exit':os.waitstatus_to_exitcode(status),'timeout':timed_out,'bytes':len(data)},bytes(data)


def main():
    if sys.platform!='linux':raise SystemExit('TUI smoke tests require an isolated Linux environment')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--only');parser.add_argument('--results',default=str(Path.home()/'tui-results-20261015'))
    args=parser.parse_args();results=Path(args.results);results.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='dev-env-tui-') as temporary:
        work=Path(temporary);home=work/'home';home.mkdir();repo=work/'repo';repo.mkdir()
        (repo/'tui-marker.txt').write_text('test content\n');(repo/'second.txt').write_text('second file\n')
        subprocess.run(['git','init','-q',str(repo)],check=True)
        subprocess.run(['git','-C',str(repo),'add','.'],check=True)
        subprocess.run(['git','-C',str(repo),'-c','user.name=VM fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture commit'],check=True)
        history=home/'history';history.write_text('ls\ncat tui-marker.txt\n')
        env={**os.environ,'HOME':str(home),'XDG_CONFIG_HOME':str(home/'.config'),'XDG_DATA_HOME':str(home/'.local/share'),
             'TERM':'xterm-256color','COLORTERM':'truecolor','MCFLY_HISTORY':str(history),'HISTFILE':str(history),
             'PWD':str(repo),'XDG_CACHE_HOME':str(home/'.cache'),'MCFLY_SESSION_ID':'tui-smoke','MCFLY_KEY_SCHEME':'vim',
             'PATH':str(Path.home()/'.local/bin')+':'+str(Path.home()/'.cargo/bin')+':/usr/local/bin:/usr/bin:/bin'}
        conf=work/'broot.hjson';conf.write_text('{}\n')
        subprocess.run(['broot','--set-install-state','refused'],env=env,cwd=repo,check=True,stdout=subprocess.DEVNULL)
        cases={
            'nvim':(['nvim','--clean','tui-marker.txt'],[(1,b':q!\r')],b'tui-marker.txt'),
            'tig':(['tig'],[(1,b'q')],b'fixture commit'),
            'vifm':(['vifm'],[(1,b':q!\r')],b'tui-marker.txt'),
            'ranger':(['ranger','--clean',str(repo)],[(1,b'q')],b'tui-marker.txt'),
            'fff':(['fff'],[(1,b'q'),(2,b'q')],b'tui-marker.txt'),
            'fzf':(['bash','-c',"printf '%s\\n' tui-marker.txt second.txt | fzf"],[(1,b'tui-marker'),(1.5,b'\r')],b'tui-marker.txt'),
            'fpp':(['bash','-c',"printf '%s\\n' tui-marker.txt second.txt | fpp"],[(1,b'q')],b'tui-marker.txt'),
            'broot':(['broot','--conf',str(conf)],[(2,b'\x03')],b'tui-marker.txt'),
            'bottom':(['btm'],[(2,b'q')],b'CPU'),
            'git-commander':(['git-commander'],[(2,b'q')],b'Staged Files'),
            'lazygit':(['lazygit'],[(1,b'\r'),(2,b'q'),(3,b'q')],b'Local branches'),
            'http-prompt':(['http-prompt','http://127.0.0.1:1'],[(2,b'exit\r'),(3,b'\x04')],b'http://127.0.0.1:1'),
            'insect':(['insect'],[(1,b'1+1\r'),(2,b'\x04')],b'= 2'),
            'mcfly':(['mcfly','search'],[(2,b'\x03')],b'McFly'),
            'glances':(['glances'],[(2,b'q')],b'CPU'),
            'tmux':(['tmux','-L','dev-env-tui-'+str(os.getpid()),'-f','/dev/null','new-session'],[(1,b'exit\r')],b'[0]'),
        }
        names=args.only.split(',') if args.only else list(cases)
        report=[]
        for name in names:
            command,steps,expected=cases[name]
            ready=b'>>>' if name=='insect' else expected
            row,data=interact(command,env,repo,steps,ready)
            plain=plain_text(data)
            row.update(app=name,rendered=expected.lower() in plain.lower())
            row['passed']=not row['timeout'] and row['exit'] in ({0,1,130} if name=='fpp' else {0,130}) and row['rendered']
            (results/(name+'.pty')).write_bytes(data)
            report.append(row);(results/'results.json').write_text(json.dumps(report,indent=2)+'\n')
            print(json.dumps(row),flush=True)
        raise SystemExit(any(not row['passed'] for row in report))

if __name__=='__main__':main()
