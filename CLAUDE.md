# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A declarative development environment setup system that configures macOS and Linux systems (natively or via Docker/VM). It installs and configures modern Unix tools, programming languages, shell utilities, and development tooling.

## Development Workspace

Continue development in this repository (`dev-env-linux`). The sibling
`dev-env-linux_bak` and `dev-env-linux.claude.bak` directories were deleted after consolidation on 2026-10-13 at the user’s request.
Their useful changes were consolidated here; see
`MERGE_NOTES.md` for provenance and conflict decisions.

## Running the Setup

```bash
# Basic setup (detects platform automatically)
./build.sh

# With options
./build.sh --optional=true         # Install optional apps
./build.sh --with-linux=docker     # Build Linux Docker image
./build.sh --enable-<app>          # Enable specific app
./build.sh --disable-<app>         # Disable specific app
./build.sh --concurrent=<n>        # Set concurrency level
./build.sh --timeout=<sec>         # Per-application timeout (exit status 124 on expiry)
```

Operations: `--operator=install` (default), `--operator=upgrade`, `--operator=uninstall`.
Installation requires Bash 4+ (the entry point uses associative arrays).
The entry point resolves the repository path itself; help and validation also work on Bash 3.2.

## Testing

```bash
# Safe shell syntax + isolated regression tests (Python 3, no network or installs)
orbctl run -m dev-env-verify-20261013 -w /home/sbrave/dev-env-linux bash scripts/check.sh

# sheath/functions_test.sh is a logging demo (intentionally exits 1), not the regression suite.

# `test.sh` is a local environment configuration, not a test suite.
```

There is no build/compile step — this is a shell scripting project.

## Architecture

### Entry Point & Orchestration
- `scripts/cli.sh` — Validates arguments without system side effects
- `build.sh` — Locates the repository, parses CLI args, sets globals (`OPTIONAL`, `CONCURRENT`, `TIMEOUT`, etc.), sources platform scripts
- `scripts/setup_macos.sh` / `scripts/setup_linux.sh` — Platform-specific orchestrators that call system and app scripts

### Installation Framework (`scripts/common_defines.sh`)
Core functions that drive the whole system:
- `execute_if_not_success <key> <cmd>` — Idempotent execution; completed steps are cached in `.dev-env-linux`
- `install <system> <tmp_dir> <app>` — Runs `preinstall_<app>`, `install_<app>`, `config_<app>` hooks if defined
- `upgrade <system> <tmp_dir> <app>` / `uninstall <system> <tmp_dir> <app>` — Same hook pattern for other operations
- `batch_wrapper` — Runs installs concurrently up to `$CONCURRENT` limit

### App Installation Scripts
Each app is defined as a set of bash functions following the naming convention:
```bash
preinstall_<system>_<app>()  { ... }  # Optional: prerequisites
install_<system>_<app>()     { ... }  # Required: main install
config_<system>_<app>()      { ... }  # Optional: post-install config
upgrade_<system>_<app>()     { ... }  # Optional: upgrade logic
uninstall_<system>_<app>()   { ... }  # Optional: removal logic
```

App scripts:
- `config/software.json` — canonical software declarations: profiles, native mappings, managed sources, requested/default versions and download templates
- `scripts/catalog.py` / `catalog.sh` — validate/query declarations and load safely quoted shell data
- `scripts/setup_linux_apps.sh` — Linux execution hooks and dispatch; reads the default selection and SDK versions from the catalog
- `scripts/setup_macos_apps.sh` — macOS apps via Homebrew
- `scripts/distro/apt.sh` / `dnf.sh` — `pkg_*` interfaces and distribution hooks; package lists load from the catalog
- `scripts/setup_linux_system.sh` — System-level config (dirs, SSH keys, distribution setup, timezone)
- `scripts/setup_macos_system.sh` — macOS `defaults` settings (trackpad, dock, etc.)

### SheAth Shell Library (`sheath/`)
A standalone shell utility library sourced into the user's shell environment:
- `constant.sh` — ANSI color codes, path constants (`CODE_PATH`, `GOPATH`, `CLONE_PATH`, `APP_PATH`, `BIN_PATH`)
- `alias.sh` — Replaces standard commands with modern alternatives (`cat`→`bat`, `ls`→`exa`, `curl`→`curlie`, etc.)
- `functions.sh` — 30+ utilities including `printf2stdout`/`printf2stderr` (9-level logging), `batch` (concurrent execution), `smart_cp`, `bak`/`unbak`, `every`, `do_if`, platform detection (`is_mac`, `is_linux`)
- `environments.sh` — PATH setup, Go/Rust env, PS1 with git branch + timestamp
- `configuration.sh` — Sources fzf, autojump, thefuck, git-flow-completion; sets vi mode

### Docker Support
- `scripts/dockerfile_ubuntu` — Ubuntu 24.04 bootstrap image; reuses build.sh for installation
- `scripts/dockerfile_centos` — CentOS Stream 10 bootstrap image; reuses build.sh for installation

### Configuration Templates (`config/`)
Dotfiles deployed during setup: `.gitconfig`, `.tmux.conf`, `.vimrc`, `.ssh_config`, `nvim/` (LazyVim-based). These use `${VARIABLE}` placeholders substituted at install time.

## Key Conventions

- **Idempotency**: Always use `execute_if_not_success` for steps that should not re-run. The cache file `.dev-env-linux` records successful commands with exact matching. Simple legacy hook entries are retained; general commands encode argument boundaries. Failed commands are not cached.
- **Adding a new app**: Declare sources/versions/platform mappings in `config/software.json`; shared backends generate hooks automatically. Add its ID to a profile only if it should be selected there. Special installation behavior still needs a hook. See `SOFTWARE_CATALOG.md`.
- **Source retention**: App scripts retain `CLONE_PATH`; installed symlinks may reference its contents.
- **Concurrent installs**: batch limits and collects child statuses; Linux package transactions are serialized to avoid APT/DNF lock races. Each application has a timeout.
- **Helper utilities**: Prefer `git_clone_nx` (clone if not exists) and `wget_nx` (download if not exists) over bare git/wget.
- **Logging**: Use `printf2stdout`/`printf2stderr` from `sheath/functions.sh` for colored, leveled output.

## Optimization Roadmap

See `OPTIMIZATION_PLAN.md` for batch status and `TECH_DEBT.md` for the diagnosis.
`TIMEOUT` is enforced per application. Upgrade/uninstall bypass install-success
cache; uninstall invalidates the corresponding install/config records. Go archives
are versioned and architecture-aware. Shell integrations use `sheath/init.sh`.
Current execution policy: all project builds, installation and tests run only in
isolated Orb VM/containers; the Mac host is for editing, transfer and management.
See `ORB_VALIDATION.md` for real integration results and untested platform scope.
