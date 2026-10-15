"""Incomplete helper behavior exercised on disposable Linux files and commands."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class TodoToolsTests(unittest.TestCase):
    def shell(self,body):
        with tempfile.TemporaryDirectory(prefix='dev-env-todo-') as directory:
            return subprocess.run(['bash','-c','source "$REPO/sheath/functions.sh"\nset -e\n'+body],
                cwd=directory,env={**os.environ,'HOME':directory,'REPO':str(ROOT)},
                capture_output=True,text=True,timeout=8)

    def ok(self,body):
        result=self.shell(body)
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)

    def test_backup_many_paths_preserves_each_version_and_dangling_links(self):
        self.ok('''printf first > 'a file'; mkdir folder; printf child > folder/item
ln -s missing dangling
bak 'a file' folder dangling > first-backups
printf second > 'a file'; bak 'a file' > second-backup
[[ $(wc -l < first-backups) == 3 ]]
first=$(head -1 first-backups); second=$(cat second-backup)
[[ "$first" != "$second" && "$first" == *.bak.* ]]
[[ $(cat "$first/payload") == first && $(cat "$second/payload") == second ]]
link=$(tail -1 first-backups); [[ -L "$link/payload" && $(readlink "$link/payload") == missing ]]
''')

    def test_restore_preserves_intervening_content_and_supports_directories(self):
        self.ok('''mkdir folder; printf old > folder/item
bak folder > backup-path
printf changed > folder/item; printf extra > folder/new
unbak "$(cat backup-path)" > saved-path
[[ $(cat folder/item) == old && ! -e folder/new ]]
[[ $(cat "$(cat saved-path)/payload/item") == changed ]]
[[ $(cat "$(cat saved-path)/payload/new") == extra ]]
[[ -d $(cat backup-path) ]]
''')

    def test_move_backup_restore_and_legacy_suffix(self):
        self.ok('''printf old > first; printf other > second
mbak first second > paths
[[ ! -e first && ! -e second && $(wc -l < paths) == 2 ]]
umbak "$(head -1 paths)" "$(tail -1 paths)"
[[ $(cat first) == old && $(cat second) == other ]]
while IFS= read -r path; do [[ ! -e "$path" ]]; done < paths
printf legacy > 'old file.bak'
unbak 'old file.bak'
[[ $(cat 'old file') == legacy ]]
if unbak first; then exit 11; fi
[[ $(cat first) == old ]]
''')

    def test_restore_identical_content_does_not_create_a_new_backup(self):
        self.ok('''printf same > file; bak file > path
unbak "$(cat path)" > output
[[ ! -s output && $(find . -maxdepth 1 -name 'file.bak.*' | wc -l) == 1 ]]
''')

    def test_log_threshold_filters_but_fatal_still_exits(self):
        self.ok('''LOG_LEVEL=warning
printf2stdout debug hidden > output
printf2stdout info hidden >> output
printf2stdout warning 'visible %s' message >> output
[[ $(cat output) == *'visible message'* && $(cat output) != *hidden* ]]
LOG_LEVEL=quiet
printf2stdout error hidden > quiet
[[ ! -s quiet ]]
if (printf2stderr fatal fatal-message); then exit 12; fi
LOG_LEVEL=typo
if printf2stdout info hidden; then exit 13; fi
''')

    def test_scd_uses_direnv_exports_and_does_not_source_dotenv(self):
        self.ok('''mkdir -p project/child
printf 'touch "$HOME/injected"' > project/.env
scd project/child
[[ "$PWD" == "$HOME/project/child" && ! -e "$HOME/injected" ]]
direnv() { [[ "$*" == 'export bash' ]] || return 2; printf 'export PROJECT_ENV=selected\\n'; }
scd ..
[[ "$PROJECT_ENV" == selected && "$PWD" == "$HOME/project" ]]
if scd missing; then exit 14; fi
[[ "$PWD" == "$HOME/project" ]]
''')

    def test_relay_uses_ssh_config_and_preserves_remote_arguments(self):
        self.ok('''mkdir bin
printf '%s\\n' '#!/bin/sh' 'printf "%s\\n" "$@" > "$HOME/ssh-args"' > bin/ssh
chmod +x bin/ssh
PATH="$HOME/bin:$PATH"
bash "$REPO/config/relay.sh" team-server 'printf hello world' '*'
[[ $(cat ssh-args) == $'team-server\\nprintf hello world\\n*' ]]
bash "$REPO/config/relay.sh" mac status
[[ $(cat ssh-args) == $'mac\\n/usr/local/bin/mutagen sync list' ]]
''')

    def test_blocked_direnv_still_unloads_previous_directory_environment(self):
        self.ok('''mkdir next
export PROJECT_ENV=previous
direnv() { printf 'unset PROJECT_ENV\\n'; return 1; }
if scd next; then exit 15; fi
[[ ! ${PROJECT_ENV+x} && "$PWD" == "$HOME/next" ]]
''')

    def test_dotfiles_deploys_an_openssh_readable_configuration_and_restores_it(self):
        self.ok('''mkdir -p .ssh
printf 'Host old-host\\n  User personal\\n' > .ssh/config
APP_PATH="$HOME/state" python3 "$REPO/scripts/dotfiles.py" install
ssh -F "$HOME/.ssh/config" -G mac > resolved
grep -qx 'hostname host.docker.internal' resolved
APP_PATH="$HOME/state" python3 "$REPO/scripts/dotfiles.py" uninstall
[[ $(cat .ssh/config) == $'Host old-host\\n  User personal' ]]
''')
