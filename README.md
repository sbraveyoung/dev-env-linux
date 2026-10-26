# dev-env-linux

Linux 开发环境安装器，支持 Ubuntu/Debian 的 APT 和 Fedora/CentOS 的 DNF。
当前目录是唯一开发目录；合并历史见 [MERGE_NOTES.md](MERGE_NOTES.md)。

## 使用

安装需 Bash 4+、普通用户和 sudo；JSON 声明由 Python 3 读取，Linux 入口会在缺失时引导安装。
macOS guest 需先准备 Python 3。下面的安装与检查命令都在隔离 Linux VM/容器内执行。
Mac 宿主仅编辑文件、传输源码和管理 Orb/Docker。

```bash
bash build.sh --help
bash build.sh --only=jq,tree --skip-system
bash build.sh --operator=upgrade --only=ccat
bash build.sh --operator=uninstall --only=ccat
bash build.sh --operator=rollback --only=ccat
```

不加 `--only` 时安装基础依赖与 76 个默认工具。`--optional=true` 追加发行版可选依赖。
`--enable-APP`、`--disable-APP` 调整工具；`--timeout=1800` 设置单项超时，超时返回 124。
包管理事务按顺序执行，避免锁竞争。`--skip-system` 跳过系统源、SSH 和时区初始化。

版本目录位于 `~/.local/share/dev-env-linux/app/managed/`，命令入口位于 `~/.local/bin/`。
Go/Cargo/Python/npm/Git/源码工具共享安装、升级、卸载和记录逻辑；卸载保留版本文件，
只删除受管理链接。`rollback` 适用于已保存前一版本的共享后端，发行版原生包由 APT/DNF 管理。
共享后端每次安装都会检查自身收据并修复入口，复用已构建版本；不被历史全局成功缓存跳过。
仓库 dotfiles 首次安装保存备份；重复 install 保留后续修改，显式 upgrade 才更新仓库配置。
卸载恢复未被修改的原文件，并保留安装后用户编辑的文件。

macOS 安装前只读识别已有 App；匹配后跳过安装和配置，保留用户的软件所有权。
各安装渠道的重复执行行为、检测范围及系统状态变更见 [INSTALLATION_SAFETY.md](INSTALLATION_SAFETY.md)。

## 版本、校验与兼容

- [software.lock.json](software.lock.json) 由 `python3 scripts/export_lock.py` 从成功安装记录生成，
  不手改。首次安装读取该锁；之后读取本机锁；`upgrade` 查询新的版本并保留旧版本。
- npm 保存完整依赖锁和 registry integrity；Python 保存依赖约束；Cargo 使用 `--locked`
  与 registry 校验；Go 使用官方模块校验数据库。Git/源码锁定确切提交。
- Go 下载按官方 API 的 SHA256 校验；rustup 按官方 `.sha256` 校验后才执行。
  原生包使用发行版签名。不同渠道的校验方式各自记录，不用下载后的自算 hash 冒充可信校验。
- Rust/Go 默认安装版本在 `config/software.json` 的对应 `apps.<ID>.version.default` 中维护，
  可用 `RUST_VERSION`/`GOLANG_VERSION` 覆盖；Rust SDK 在私有 `app/rust-sdk`，保留用户原 SDK。
  Go 版本自动查询需显式设置 `SKIP_VERSION_CHECK=false`。
- 共享后端可设置 `apps.<ID>.managed.version` 固定期望版本，优先于安装锁；未设置时保留现有锁/升级规则。
- `exa` 对应维护中的 `eza`；APT 的 fd/bat 命令名有兼容入口。
- insect 使用官方 npm CLI，支持 ARM；Squoosh 的兼容层处理 Node fetch 和 VM worker 数量。
- forgit 保持原配置的下载停用状态，不进入默认队列。grv 仍仅支持配置中的 x64 资产，
  在 ARM 上显式失败。独立的 `lazygit` 是已验证的 ARM Git TUI 选择；不会替换 grv 的名称。
  ImageMagick、dive、trash-cli、FlameGraph、lazygit 可手动选择，默认不启用。

完整实测范围、结果与限制见 [FULL_VALIDATION.md](FULL_VALIDATION.md)。原生包版本清单
仅记录验证时状态，软件源移除旧版本后不能保证仅凭版本号重建同一系统。
本轮 Fedora/CentOS 全矩阵、TUI、GC 和离线恢复见 [MAINTENANCE_VALIDATION.md](MAINTENANCE_VALIDATION.md)。

## 隔离验证与 CI

```bash
orbctl run -m dev-env-verify-20261013 -w /home/sbrave/dev-env-linux bash scripts/check.sh
orbctl run -m dev-env-verify-20261013 -w /home/sbrave/dev-env-linux python3 tests/full_install.py
```

`check.sh` 执行 Shell 语法、Python 回归测试和 ShellCheck。`full_install.py` 逐项真实安装，
将结果和日志写入 VM 的 `~/dev-env-full-results/`；需要一次性、可丢弃的环境。
CI 在 push/PR 检查 Ubuntu 与 Fedora；手动工作流在 ARM runner 全量实装并保留日志。
所有 Actions 固定提交，凭据不持久化到 checkout。
macOS 隔离方法及仅手动触发、尚未执行的远端工作流见 [MACOS_TESTING.md](MACOS_TESTING.md)。
真实 macOS 功能不能用 Linux mock 或普通 Linux 容器认证。

也可以通过 Orb 的 Linux Docker daemon 构建无宿主挂载的开发容器：

```bash
docker build -t dev-env-linux:local -f scripts/dockerfile_ubuntu .
docker run -dit --name dev-env dev-env-linux:local bash
docker exec -it dev-env bash
```

CentOS 使用 `scripts/dockerfile_centos`（Stream 10）。容器内仓库路径 `/opt/dev-env-linux`，
普通用户 `developer`。无需 privileged、host network、宿主目录共享或明文密码构建参数。

## 维护

以下命令仅在可丢弃的 Linux 环境中运行：

```bash
python3 scripts/managed_gc.py --only=ccat --keep=1          # 仅预览
python3 scripts/managed_gc.py --only=ccat --keep=1 --apply  # 显式删除候选
python3 scripts/native_bundle.py create /tmp/native-bundle --packages=jq,tree,tmux
python3 scripts/native_bundle.py verify /tmp/native-bundle
python3 scripts/native_bundle.py restore /tmp/native-bundle          # 仅预览
python3 scripts/native_bundle.py restore /tmp/native-bundle --apply  # 修改接收环境
python3 tests/tui_smoke.py --only=nvim,tig,broot,tmux
```

GC 保护当前、前一版本、本机/仓库锁和所有命令链接；未知目录、损坏状态和软链不会被当成可删除版本。
`--keep` 指额外保留的未引用版本数，不会覆盖上述保护。不会清理 Rust SDK、下载缓存或用户数据。
离线包必须来自可信 donor；SHA256 清单检测损坏，不能认证被整体替换的清单/公钥。
接收环境须匹配发行版、版本和架构；恢复会安装根包及依赖，并校验根包精确版本。
APT 创建依赖闭包使用空状态，DNF 使用完整依赖下载及本地 repo；DNF 创建需 `createrepo_c`。
归档 APT bundle 时只携带 manifest.json 和 archives/*.deb，排除 partial/、lock 和 empty-status。
DNF bundle 同时携带 repodata 与 RPM-GPG-KEYS。小规模验证不等于整个发行版或所有原生包已离线保存。

[config/software.json](config/software.json) 统一声明安装分组、平台/发行版映射、来源、SDK 默认版本和下载模板。
查询/校验及配置示例见 [SOFTWARE_CATALOG.md](SOFTWARE_CATALOG.md)。原 scripts/software.json 已迁移移除。
合并其他发行版的真实收据时，在 VM 用 `scripts/export_lock.py --merge=donor.json` 生成；
本机记录优先，donor 只补缺失工具并校验来源，生成的锁文件不手改。
[archive/README.md](archive/README.md) 说明本地历史归档；旧目录内容与权限保留，带 SHA256 清单。
日志、旧缓存和 todo 已移到忽略的 `.local/history/2026-10-14/`；本地 test.sh 保持私有。
计划与债务见 [OPTIMIZATION_PLAN.md](OPTIMIZATION_PLAN.md)、[TECH_DEBT.md](TECH_DEBT.md)。

活动 TODO、已补齐的功能和仍需来源信息的项目见 [TODO_STATUS.md](TODO_STATUS.md)。
