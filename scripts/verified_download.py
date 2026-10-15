#!/usr/bin/env python3
"""Verify downloads against a publisher-provided SHA256 before use."""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.catalog import load_or_exit


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def verify(path, expected):
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if len(expected) != 64 or digest != expected.lower():
        raise ValueError('publisher SHA256 mismatch: '+str(path))


if __name__ == '__main__':
    mode, path, version, arch = sys.argv[1:]
    if mode == 'go':
        url=load_or_exit()['apps']['golang']['checksum_url']
        releases = json.loads(fetch(url))
        expected = next(asset['sha256'] for release in releases if release['version']=='go'+version
                        for asset in release['files'] if asset['filename']=='go'+version+'.linux-'+arch+'.tar.gz')
    elif mode == 'rustup':
        expected = fetch(version+'.sha256').decode().split()[0]
    else:
        raise ValueError('unknown publisher')
    verify(path,expected)
    Path(path+'.verified.json').write_text(json.dumps({'sha256':expected,'publisher':mode,'source':version})+'\n')
