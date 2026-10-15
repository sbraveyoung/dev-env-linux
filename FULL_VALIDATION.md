# 全量推进与隔离验收（2026-10-14）

本页保留 2026-10-14 的历史范围。2026-10-15 已完成 DNF 全矩阵、TUI、显式 GC 和原生包离线恢复；
最新证据及范围见 [MAINTENANCE_VALIDATION.md](MAINTENANCE_VALIDATION.md)，生成锁现为 65 项。

五项推进已落地：逐项实装、共享生命周期、DNF 实测、可信校验与版本锁/回滚、CI 与历史归档。
所有安装、编译和测试均在隔离 Linux 内执行。Mac 仅编辑/传输源码及管理 Orb/Docker。

## 实测范围

| 环境 | 隔离方式 | 验证结果 |
| --- | --- | --- |
| Ubuntu 24.04 ARM64 `dev-env-verify-20261013` | Orb `--isolated`，2 CPU / 4 GB / 32 GB，无宿主共享 | 76/76 默认工具实装通过；基础与可选依赖实装通过 |
| Fedora 44 ARM64 `dev-env-fedora-20261014` | Orb `--isolated`，2 CPU / 3 GB / 40 GB，无宿主共享 | 全部基础依赖实装；jq/tree/tmux 安装、升级、卸载、重装；mdv/zx 实装；ffmpeg-free 实装 |
| CentOS Stream10 ARM64 `dev-env-centos10-20261014` | Orb `--isolated`，2 CPU / 3 GB / 40 GB，无宿主共享 | EPEL/CRB/RPMFusion 初始化；全部基础依赖实装；jq/tree/tmux 完整生命周期；mdv/zx 实装 |
| Ubuntu 与 CentOS Stream10 Docker 镜像 | Orb Linux daemon；普通 developer；检查容器无宿主挂载 | 两个 Dockerfile 构建通过；各 41 个回归测试通过 |

三个 VM 各通过 41 个回归测试、30 个 Shell 文件语法检查及 ShellCheck warning/error 检查。
容器同样运行语法及回归测试；容器基础镜像未安装 ShellCheck，静态 lint 由 VM 和 CI 执行。

逐项结果：[ubuntu-apps.json](validation/2026-10-14/ubuntu-apps.json)。
原生包清单记录依赖闭包，不是顶层应用数量：Ubuntu 1660、Fedora 1073、CentOS 872 个包。
对应清单位于 [validation/2026-10-14](validation/2026-10-14)。

## 生命周期、运行与重建

- ccat、mdv、insect、diff-so-fancy、mcfly 分别代表 Go、Python、npm、Git、Cargo，均通过真实安装→升级→卸载→重装。
- 独立前缀实际构建 ccat v1.0.0 与 v1.1.0，回滚后 current/lock 与命令均指向 v1.0.0。
- ImageMagick 从固定 Git 提交构建并完成升级、卸载、重装；实际 `magick -version` 可运行。
  当前验证源码为 `892090606554b532a99535a8d88e0148f5dbf20b`，输出 7.1.2-34 (Beta)。这是可选源码快照，默认不启用。
- 私有 Rust 1.99.0 完成升级、回滚、卸载、重装；原来的 `~/.cargo` SDK 保留。
- 使用空白前缀按仓库锁重建 ccat/mdv/insect/diff-so-fancy；另用私有 Rust SDK 重建 pastel 0.12.0，命令运行通过。
- insect 真实计算 `1+1=2`；Squoosh 正式入口将有效的 16×16 PNG 转成 JPEG。
- Go 1.27.2 ARM64 压缩包和 rustup 安装器通过官方发布 SHA256 校验；损坏下载拒绝测试通过。
- dotfiles 测试验证原文件恢复、连续升级保留原备份、用户改动保留；链接保护、失败激活不产生部分链接与回滚更新锁均有回归覆盖。

## 修复的实际失败

首次实装遇到 APT 锁竞争与 npm 尚未就绪；准备完成后重试通过。后续检查发现并修复：

- insect 的旧 x64 资产路径不能用于 ARM，改用官方 npm CLI；npm hoisting 破坏其相对依赖路径，改为嵌套安装。
- Squoosh 使用文件路径载入 WASM，与 Node 18 原生 fetch 冲突；专用兼容层关闭该进程的 fetch，并限制按宿主核心数创建的 worker。
- scoped npm bin 字段需要规范化；只导出软件自身入口，不导出全部传递依赖命令。
- xh 注册表 TLS 握手超时；API 增加有界重试。
- ImageMagick 全历史克隆中断；改为只拉取固定提交，使用 HTTP/1.1 与有界重试。
- Ubuntu `libfreetype6-dev` 不再有候选，改为 `libfreetype-dev`；APT 后续安装关闭 recommends。
- CentOS10 缺失 `pcre-devel`，改为 `pcre2-devel`；DNF5 仓库配置与包组命令已适配。
- 旧 `config/setup_centos.sh` 现在转发到维护中的入口，旧内容保存在本地归档；不再运行重复且过时的全局安装流程。
- Rust SDK 改为私有目录；Vim 不再移动 `/usr/bin/vim`；Python/pip 兼容入口不改 `/usr/bin`。

## 版本、CI 与历史目录

[software.lock.json](software.lock.json) 保存 41 个共享后端安装记录，使用 VM 中
`scripts/export_lock.py` 生成。npm 带完整依赖锁，Python 带依赖约束，Go/Cargo 使用各自的校验机制，Git/源码固定提交。
原生包由 APT/DNF 管理并保存验证时版本。它们的旧版本可能从上游移除，因此这不是完全离线、跨平台逐字节重建保证。

[check.yml](.github/workflows/check.yml) 在 push/PR 检查 Ubuntu/Fedora；
[full-install.yml](.github/workflows/full-install.yml) 手动在 ARM runner 全量安装并归档日志。
Actions 固定具体提交，checkout 不持久化凭据。未提交或推送，本次没有触发远端 GitHub Actions。

`linux/`、`scripts.bak/`、`sheath.bak/` 及旧 CentOS 脚本完整归档到忽略的 `archive/legacy/`；
21 个文件按原内容 SHA256 验证。旧缓存、日志、output、todo 保存到 `.local/history/2026-10-14/`。
本地 test.sh 保持私有，不进入 Git、Docker 构建上下文或 VM 源码传输。

## 保留的限制

- forgit 保持原配置的下载停用状态，从默认队列移除；显式选择时报告原因。
- grv 仍只有配置中的 x64 资产，在 ARM 显式返回不支持；不把此项算成安装成功。
- CentOS Stream9 的 Orb 初始化两次因上游 BaseOS 元数据 SHA512 不匹配失败，未关闭校验；改用 Stream10 完成验证。
- 76/76 表示真实安装成功，额外运行检查覆盖上述入口；未逐一交互验收所有 TUI，也未测试全部软件在 Fedora/CentOS 的组合。
- 旧版本目录为回滚保留，暂不自动清除；所有环境保留供复查，VM 内原始日志保存在用户家目录。
