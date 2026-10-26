#!/usr/bin/env python3
"""Read-only detection of external macOS applications; never adopt their ownership."""
import argparse
import os
from pathlib import Path
import plistlib
import sys
from xml.parsers.expat import ExpatError

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.catalog import load


def bundle_info(bundle):
    """A matching name alone is insufficient: require a complete executable bundle."""
    try:
        with (bundle/'Contents/Info.plist').open('rb') as source:info=plistlib.load(source)
        if not isinstance(info,dict) or info.get('CFBundlePackageType')!='APPL':return None
        identifier=info.get('CFBundleIdentifier');name=info.get('CFBundleExecutable')
        if not isinstance(identifier,str) or not identifier or not isinstance(name,str) or not name:return None
        executable=bundle/'Contents/MacOS'/name
        if (not executable.is_file() or not os.access(executable,os.X_OK) or
                not executable.resolve().is_relative_to(bundle.resolve())):return None
        return info
    except (FileNotFoundError,NotADirectoryError,plistlib.InvalidFileException,ExpatError,ValueError,RuntimeError):
        return None


def existing_application(name,data):
    spec=data['apps'].get(name,{}).get('darwin',{})
    names=spec.get('app_bundles',[])
    if not names and spec.get('installer')=='qt':names=[Path(spec['bundle']).name]
    identifiers=spec.get('bundle_ids',[])
    if not names and not identifiers:return None
    home=Path.home()
    roots=[Path(os.environ.get('DEV_ENV_APPLICATIONS_DIR','/Applications')),home/'Applications']
    roots.extend(Path(p).expanduser() for p in spec.get('app_directories',[]))
    managed=Path(os.environ.get('APP_PATH',str(home/'.local/share/dev-env-linux/app')))/'macos'/name
    for root in dict.fromkeys(roots):
        try:
            candidates=sorted(root.iterdir())
            # Common installed bundles can live one level below Applications (e.g. Utilities).
            for directory in list(candidates):
                if directory.is_dir() and not directory.name.endswith('.app') and not directory.is_symlink():
                    candidates.extend(sorted(directory.glob('*.app')))
        except (FileNotFoundError,NotADirectoryError):continue
        for bundle in candidates:
            if not bundle.name.endswith('.app'):continue
            if bundle.is_symlink() and bundle.resolve().is_relative_to(managed.resolve()):continue
            info=bundle_info(bundle)
            if info and (info['CFBundleIdentifier'] in identifiers if identifiers else bundle.name in names):
                return bundle
    return None


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('application')
    args=parser.parse_args()
    try:application=existing_application(args.application,load())
    except (OSError,ValueError,RuntimeError) as error:parser.exit(2,str(error)+'\n')
    if application is None:parser.exit(1)
    print(application)
