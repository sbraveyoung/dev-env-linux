#!/usr/bin/env python3
"""Create editor/terminal defaults without replacing existing user configuration."""
import argparse
import os
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]


def create_default(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive creation also preserves symlinks, including dangling ones.
    try:
        with target.open('xb') as output:output.write(source.read_bytes())
    except FileExistsError:
        print('preserved existing configuration: '+str(target))


def configure(name):
    home=Path.home()
    if name=='kitty':
        target=Path(os.environ.get('XDG_CONFIG_HOME',str(home/'.config')))/'kitty/kitty.conf'
        create_default(ROOT/'config/kitty/kitty.conf',target)
    else:
        create_default(ROOT/'config/vscode/settings.json',home/'Library/Application Support/Code/User/settings.json')
        applications=Path(os.environ.get('DEV_ENV_APPLICATIONS_DIR','/Applications'))
        candidates=[applications/'Visual Studio Code.app',home/'Applications/Visual Studio Code.app']
        source=next((p/'Contents/Resources/app/bin/code' for p in candidates
                     if (p/'Contents/Resources/app/bin/code').is_file()),None)
        if source is None:
            source=Path(shutil.which('code')) if shutil.which('code') else None
        if source is None:raise ValueError('VS Code CLI was not found in the installed application')
        target=Path(os.environ.get('BIN_PATH',str(home/'.local/bin')))/'code'
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() or target.is_symlink():
            if target.resolve()!=source.resolve():print('preserved existing CLI: '+str(target))
        else:target.symlink_to(source)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('application',choices=['kitty','vscode'])
    args=parser.parse_args()
    try:configure(args.application)
    except (OSError,ValueError) as error:parser.exit(1,str(error)+'\n')
