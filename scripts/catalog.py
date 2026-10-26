#!/usr/bin/env python3
"""Read-only software declarations and safely quoted data for shell consumers."""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import string
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'config/software.json'
BACKENDS={'go','cargo','pip','npm','git','source'}


def unique_object(pairs):
    result={}
    for name,value in pairs:
        if name in result:raise ValueError('duplicate JSON key: '+name)
        result[name]=value
    return result


def object_at(value,label,required=(),allowed=None):
    if not isinstance(value,dict):raise ValueError(label+': expected an object')
    missing=set(required)-value.keys()
    if missing:raise ValueError(label+': missing '+', '.join(sorted(missing)))
    if allowed is not None:
        unknown=value.keys()-set(allowed)
        if unknown:raise ValueError(label+': unknown field '+', '.join(sorted(unknown)))
    return value


def token(value,label,pattern=r'[A-Za-z0-9_][A-Za-z0-9_.+*:@/-]*'):
    if not isinstance(value,str) or not re.fullmatch(pattern,value):raise ValueError(label+': invalid value')


def names(values,label,pattern=r'[A-Za-z0-9_][A-Za-z0-9_.+*:@/-]*'):
    if not isinstance(values,list):raise ValueError(label+': expected an array')
    for value in values:token(value,label,pattern)


def template(value,label,url=False):
    if not isinstance(value,str) or not value or any(ord(c)<32 or ord(c)==127 for c in value):
        raise ValueError(label+': invalid template')
    try:
        for _,field,spec,conversion in string.Formatter().parse(value):
            if field is not None and (field not in {'version','release','arch','target'} or spec or conversion):
                raise ValueError('unsupported placeholder')
        if url:
            parts=urlsplit(value)
            if parts.scheme!='https' or not parts.hostname or parts.username or parts.password:
                raise ValueError('expected an HTTPS URL')
    except ValueError as error:raise ValueError(label+': '+str(error)) from None


def relative_path(value,label):
    if (not isinstance(value,str) or not value or any(ord(c)<32 for c in value) or
            PurePosixPath(value).is_absolute() or '..' in PurePosixPath(value).parts):
        raise ValueError(label+': expected a relative path without ..')


def version_at(value,label):
    version=object_at(value,label,('variable','default'),{'variable','default','latest'})
    token(version['variable'],label+'.variable',r'[A-Z][A-Z0-9_]*_VERSION')
    token(version['default'],label+'.default',r'[A-Za-z0-9][A-Za-z0-9._+-]*')
    if 'latest' in version:
        latest=object_at(version['latest'],label+'.latest',('provider','url'),{'provider','url'})
        if latest['provider'] not in ('go','github'):raise ValueError(label+'.latest.provider: unsupported provider')
        template(latest['url'],label+'.latest.url',url=True)


def managed_at(value,label):
    spec=object_at(value,label,('backend','package'),
                   {'backend','package','version','commands','aliases','bin_scripts','ref','cargo_profile','note','migration'})
    if not isinstance(spec['backend'],str) or spec['backend'] not in BACKENDS:
        raise ValueError(label+'.backend: unsupported backend')
    token(spec['package'],label+'.package',r'[A-Za-z0-9_@][A-Za-z0-9_.+*:@/~-]*')
    if 'version' in spec:token(spec['version'],label+'.version',r'[A-Za-z0-9][A-Za-z0-9._+-]*')
    command_pattern=r'[A-Za-z0-9_][A-Za-z0-9_.+-]*'
    if 'commands' in spec:
        for command,relative in object_at(spec['commands'],label+'.commands').items():
            token(command,label+'.commands',command_pattern)
            if (not isinstance(relative,str) or not relative or '\x00' in relative or
                    PurePosixPath(relative).is_absolute() or '..' in PurePosixPath(relative).parts):
                raise ValueError(label+'.commands.'+command+': expected a relative path without ..')
    if 'aliases' in spec:
        for alias,original in object_at(spec['aliases'],label+'.aliases').items():
            token(alias,label+'.aliases',command_pattern);token(original,label+'.aliases',command_pattern)
    if 'bin_scripts' in spec:names(spec['bin_scripts'],label+'.bin_scripts',command_pattern)
    if 'cargo_profile' in spec:
        for key,value in object_at(spec['cargo_profile'],label+'.cargo_profile').items():
            token(key,label+'.cargo_profile',r'[a-z][a-z0-9_]*')
            token(value,label+'.cargo_profile.'+key,r'[A-Za-z0-9_.+-]+')
    for key in ['ref','note','migration']:
        if key in spec and (not isinstance(spec[key],str) or not spec[key]):raise ValueError(label+'.'+key+': expected text')


def load(path=None):
    """Validate the entire declaration before returning data to any consumer."""
    path=path if path is not None else os.environ.get('DEV_ENV_SOFTWARE_CATALOG',DEFAULT)
    data=json.loads(Path(path).read_text(),object_pairs_hook=unique_object)
    fields={'schema','apps','profiles','drivers','backend_dependencies','bootstrap'}
    object_at(data,'catalog',fields,fields)
    if type(data['schema']) is not int or data['schema']!=1:raise ValueError('unsupported catalog schema')
    apps=object_at(data['apps'],'apps')
    for name,app in apps.items():
        token(name,'app ID',r'[A-Za-z0-9_][A-Za-z0-9_.+@-]*')
        label='apps.'+name
        object_at(app,label,allowed={'managed','native','darwin','version','download_url','checksum_url','source_url',
                                    'plugin_url','targets','architectures','module','legacy_python_package','status','note'})
        if 'managed' in app:managed_at(app['managed'],label+'.managed')
        for platform,package in object_at(app.get('native',{}),label+'.native').items():
            token(platform,label+'.native platform',r'[a-z][a-z0-9_-]*');names([package],label+'.native.'+platform)
        if 'darwin' in app:
            mac=object_at(app['darwin'],label+'.darwin',('backend',),
                          {'backend','package','implemented','version','download_url','archive','bundle','font_family','font_package','font_tap','tap','installer','source_url','revision','project','qt_package','brew_dependencies','library_subdir','link_packages','patches','app_bundles','bundle_ids','app_directories'})
            if 'app_bundles' in mac:
                names(mac['app_bundles'],label+'.darwin.app_bundles',r'[^/\\\x00-\x1f]+\.app')
                if any(v.startswith('.') for v in mac['app_bundles']):raise ValueError(label+'.darwin.app_bundles: invalid basename')
            if 'bundle_ids' in mac:names(mac['bundle_ids'],label+'.darwin.bundle_ids',r'[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+')
            if 'app_directories' in mac:
                if not isinstance(mac['app_directories'],list):raise ValueError(label+'.darwin.app_directories: expected an array')
                for directory in mac['app_directories']:
                    if (not isinstance(directory,str) or not directory.startswith(('/', '~/')) or
                            '..' in PurePosixPath(directory).parts or any(ord(c)<32 for c in directory)):
                        raise ValueError(label+'.darwin.app_directories: expected absolute or home-relative directory')
            if mac['backend'] not in ('brew','hook'):raise ValueError(label+'.darwin.backend: unsupported backend')
            if mac['backend']=='brew':names([mac.get('package')],label+'.darwin.package')
            if 'implemented' in mac and type(mac['implemented']) is not bool:raise ValueError(label+'.darwin.implemented: expected a boolean')
            for key in ['font_package','font_tap','tap']:
                if key in mac:names([mac[key]],label+'.darwin.'+key)
            if 'font_family' in mac and not isinstance(mac['font_family'],str):raise ValueError(label+'.darwin.font_family: expected text')
            if 'installer' in mac:
                if mac['backend']!='hook' or mac['installer']!='qt':raise ValueError(label+'.darwin.installer: expected a Qt hook')
                required={'source_url','revision','project','bundle','qt_package','brew_dependencies'}
                object_at(mac,label+'.darwin',required)
                token(mac['revision'],label+'.darwin.revision',r'[0-9a-f]{40}')
                for key in ['project','bundle','library_subdir']:
                    if key in mac:relative_path(mac[key],label+'.darwin.'+key)
                names([mac['qt_package']],label+'.darwin.qt_package')
                names(mac['brew_dependencies'],label+'.darwin.brew_dependencies')
                names(mac.get('patches',[]),label+'.darwin.patches',r'[A-Za-z0-9_][A-Za-z0-9_.+-]*')
                names(mac.get('link_packages',[]),label+'.darwin.link_packages',r'[A-Za-z0-9_][A-Za-z0-9_.+-]*')
        for owner,prefix in [(app,label),(app.get('darwin',{}),label+'.darwin')]:
            if 'version' in owner:version_at(owner['version'],prefix+'.version')
            for key,value in owner.items():
                if key.endswith('_url') or key in {'archive','bundle'}:template(value,prefix+'.'+key,url=key.endswith('_url'))
        if 'targets' in app:
            for arch,target in object_at(app['targets'],label+'.targets').items():
                token(arch,label+'.targets');token(target,label+'.targets.'+arch)
        if 'architectures' in app:names(app['architectures'],label+'.architectures')
        for key in ['module','legacy_python_package','status','note']:
            if key in app and not isinstance(app[key],str):raise ValueError(label+'.'+key+': expected text')
    required_profiles={'linux-default','linux-manual','darwin-base','darwin-optional','darwin-development'}
    for profile,values in object_at(data['profiles'],'profiles',required_profiles).items():
        label='profiles.'+profile
        token(profile,label);names(values,label)
        if len(values)!=len(set(values)) or any(name not in apps for name in values):raise ValueError(label+': invalid profile references')
        if profile.startswith('darwin-') and any('darwin' not in apps[name] for name in values):
            raise ValueError(label+': app has no Darwin declaration')
    for distro,driver in object_at(data['drivers'],'drivers',('apt','dnf')).items():
        label='drivers.'+distro
        keys={'base_packages','optional_packages','ssh_client','package_ext'}
        object_at(driver,label,keys,keys)
        for key in ['base_packages','optional_packages']:names(driver[key],label+'.'+key)
        names([driver['ssh_client']],label+'.ssh_client')
        if driver['package_ext'] not in ('deb','rpm'):raise ValueError(label+'.package_ext: expected deb or rpm')
    for backend,distros in object_at(data['backend_dependencies'],'backend_dependencies').items():
        label='backend_dependencies.'+backend
        if backend not in BACKENDS:raise ValueError(label+': unsupported backend')
        for distro,values in object_at(distros,label,('apt','dnf')).items():names(values,label+'.'+distro)
    for name,bootstrap in object_at(data['bootstrap'],'bootstrap',('homebrew',)).items():
        label='bootstrap.'+name
        object_at(bootstrap,label,('install_url',),{'install_url'})
        template(bootstrap['install_url'],label+'.install_url',url=True)
    return data


def load_or_exit():
    """CLI consumers reject invalid declarations before reading or mutating state."""
    try:return load()
    except (OSError,ValueError) as error:raise SystemExit('catalog: '+str(error)) from None


def managed_apps():
    return {name:app['managed'] for name,app in load_or_exit()['apps'].items() if 'managed' in app}


def shell_array(name,values):
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',name):raise ValueError('invalid shell array name')
    return name+'=('+ ' '.join(shlex.quote(value) for value in values)+')'


def native(app,distro,identity):
    packages=app.get('native',{})
    return packages.get(identity,packages.get(distro))


def defaults(data,platform):
    result=[]
    for app in data['apps'].values():
        owner=app if platform=='linux' else app.get('darwin',{})
        if version:=owner.get('version'):
            variable=version['variable']
            result.append('if [[ -z ${'+variable+':-} ]]; then '+variable+'='+shlex.quote(version['default'])+'; fi')
    return '\n'.join(result)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',default=os.environ.get('DEV_ENV_SOFTWARE_CATALOG',str(DEFAULT)))
    commands=parser.add_subparsers(dest='operation',required=True)
    commands.add_parser('validate')
    commands.add_parser('managed')
    commands.add_parser('brew')
    commands.add_parser('qt')
    p=commands.add_parser('bootstrap');p.add_argument('name')
    p=commands.add_parser('profile');p.add_argument('name');p.add_argument('--shell-var')
    p=commands.add_parser('defaults');p.add_argument('--platform',choices=['linux','darwin'],required=True)
    p=commands.add_parser('latest');p.add_argument('--platform',choices=['linux'],default='linux')
    p=commands.add_parser('native');p.add_argument('--distro',required=True);p.add_argument('--distro-id',default='')
    p=commands.add_parser('packages');p.add_argument('--distro',required=True)
    p=commands.add_parser('dependencies');p.add_argument('backend');p.add_argument('--distro',required=True)
    p=commands.add_parser('field');p.add_argument('app');p.add_argument('path')
    for flag in ['version','arch','target']:p.add_argument('--'+flag,default='')
    p=commands.add_parser('macos');p.add_argument('--optional',choices=['true','false'],default='false');p.add_argument('--development',choices=['true','false'],default='true')
    p=commands.add_parser('list');p.add_argument('--platform',choices=['linux','darwin'],default='linux');p.add_argument('--distro',default='apt');p.add_argument('--distro-id',default='')
    args=parser.parse_args()
    try:
        data=load(args.config);op=args.operation;apps=data['apps']
        if op=='validate':return
        if op=='managed':print(' '.join(name for name,app in apps.items() if 'managed' in app));return
        if op=='brew':
            for name,app in apps.items():
                mac=app.get('darwin',{})
                if mac.get('backend')=='brew':print('\t'.join([name,mac['package'],mac.get('tap','')]))
            return
        if op=='qt':print(' '.join(name for name,app in apps.items() if app.get('darwin',{}).get('installer')=='qt'));return
        if op=='bootstrap':print(data['bootstrap'][args.name]['install_url']);return
        if op=='profile':
            values=data['profiles'][args.name]
            print(shell_array(args.shell_var,values) if args.shell_var else json.dumps(values));return
        if op=='defaults':print(defaults(data,args.platform));return
        if op=='latest':
            for app in apps.values():
                version=app.get('version',{});latest=version.get('latest')
                if latest:print('\t'.join([version['variable'],latest['provider'],latest['url']]))
            return
        if op=='native':
            for name,app in apps.items():
                if package:=native(app,args.distro,args.distro_id):print(name+'\t'+package)
            return
        if op=='packages':
            driver=data['drivers'][args.distro]
            print(shell_array('DISTRO_PKG_APPS',driver['base_packages']))
            print(shell_array('DISTRO_OPTIONAL_PKG_APPS',driver['optional_packages']))
            print('DISTRO_NATIVE_APPS=()\ndeclare -A DISTRO_NATIVE_PACKAGES=()')
            print('DISTRO_PACKAGE_EXT='+shlex.quote(driver['package_ext']))
            print('DISTRO_SSH_CLIENT='+shlex.quote(driver['ssh_client']));return
        if op=='dependencies':
            print(shell_array('CATALOG_DEPENDENCIES',data['backend_dependencies'][args.backend][args.distro]));return
        if op=='field':
            value=apps[args.app]
            for part in args.path.split('.'):value=value[part]
            if not isinstance(value,str):raise ValueError('field is not text')
            print(value.format(version=args.version,release=args.version.split('_')[0],arch=args.arch,target=args.target));return
        if op=='macos':
            selected=list(data['profiles']['darwin-base'])
            if args.optional=='true':selected+=data['profiles']['darwin-optional']
            if args.development=='true':selected+=data['profiles']['darwin-development']
            selected=list(dict.fromkeys(selected))
            print(shell_array('brew_apps',[name for name in selected if apps[name]['darwin']['backend']=='brew']))
            print(shell_array('customized_apps',[name for name in selected if apps[name]['darwin']['backend']=='hook']))
            print(defaults(data,'darwin'));return
        lock_path=ROOT/'software.lock.json'
        locked=json.loads(lock_path.read_text()) if lock_path.exists() else {}
        rows=[]
        linux_ids=set(data['profiles']['linux-default']+data['profiles']['linux-manual'])
        for name,app in apps.items():
            if args.platform=='darwin':
                if not (spec:=app.get('darwin')):continue
                backend=spec['backend'];package=spec.get('package',name)
                fallback='Homebrew managed' if backend=='brew' else ('not implemented' if spec.get('implemented') is False else 'hook managed')
                version=spec.get('version',{}).get('default',spec.get('revision',fallback))
                enabled=name in data['profiles']['darwin-base']+data['profiles']['darwin-development']
            else:
                if name not in linux_ids and 'managed' not in app and 'native' not in app:continue
                spec=app.get('managed',{});package=native(app,args.distro,args.distro_id)
                backend='native' if package else spec.get('backend','hook')
                package=package or spec.get('package',name)
                version='distro managed' if backend=='native' else app.get('version',{}).get('default',spec.get('version',locked.get(name,{}).get('version','registry latest / hook')))
                enabled=name in data['profiles']['linux-default']
            rows.append({'app':name,'default':enabled,'backend':backend,'package':package,'version':version})
        print(json.dumps(rows,indent=2))
    except (OSError,ValueError,KeyError,TypeError) as error:parser.exit(2,'catalog: '+str(error)+'\n')

if __name__=='__main__':main()
