# 剩余维护任务验收（2026-10-15）

本轮完成 DNF 默认全矩阵、受管理版本 GC、代表原生包离线恢复、TUI 烟测与 ARM Git TUI 替代。
Mac 宿主仅编辑/传输文件及管理 Orb/Docker，所有项目执行均在隔离 Linux 内。
macOS 仅做 Linux 模拟和远端工作流准备，未执行真实 macOS 作业。

## 最终矩阵

| 环境 | 默认应用 | 回归/静态检查 | TUI |
| --- | --- | --- | --- |
| Ubuntu 24.04 ARM64 `dev-env-verify-20261013` | 76/76 | 61 测试、30 Shell 语法、ShellCheck 通过 | 16/16，含可选 lazygit |
| Fedora 44 ARM64 `dev-env-fedora-20261014` | 76/76 | 同上 | 15/15 |
| CentOS Stream10 ARM64 `dev-env-centos10-20261014` | 76/76 | 同上 | 15/15 |
| Ubuntu/CentOS Docker 镜像 `*:20261015` | 本轮未在镜像全量安装 | 各 61 测试、30 Shell 语法通过 | 未在容器重做 TUI |

三个 VM 均沿用 --isolated、无宿主共享目录。检查容器使用 --network=none，无宿主挂载、非 privileged；
镜像构建和实际恢复通过 Orb Linux daemon。容器没有 ShellCheck，lint 结果来自 VM。
全量安装先真实构建/下载，修复失败后运行整个队列；最终复验复用已经成功的版本和原生包缓存。
这不是每次重新下载全部工具的测量，也不代表所有工具的完整业务功能均已交互验收。

逐项 JSON、完整回归输出和离线恢复日志位于 [validation/2026-10-15](validation/2026-10-15)。
TUI 使用临时 HOME/XDG 目录、临时 Git 仓库和 Linux 原生命令 PATH，排除 Orb 宿主命令转发路径。
实际检查界面标记、按键和退出；insect 检查 1+1=2，fzf 输入筛选，PathPicker 的取消退出码 1 是预期。
数据库连接、网络会话、文件管理器完整操作和 GUI 不属于本次烟测。

## 修复了哪些实际问题

- Fedora gron/cheat 遇到 Go 代理 TLS 超时，重新下载后成功，未关闭完整性校验。
- broot 的 fat LTO 在 3 GB DNF VM 中被 OOM kill，cgroup memory.events 有 oom_kill 记录。
  仅 broot 改为关闭 release LTO、16 个 codegen units；Cargo 两个编译任务，Fedora/CentOS 实际重建成功。
- CentOS 源没有 axel 候选；使用私有源码后端，补齐 gettext-devel/autoconf-archive。
  上游 v2.17.14/HEAD 要求 Autoconf 2.72，而 EL 提供 2.71；选择兼容的 v2.17.13，
  锁定提交 3f397e37d18d1a7f5d27a299d0c16c73e5dfcfe5，不修改上游生成物。
  升级、卸载、重装和 axel --version 实测通过；此源码版本随 catalog 的 ref 更新。
- ranger-fm 使用 setuptools 旧式 scripts，不在 console_scripts 中。
  catalog 声明 bin_scripts，安装器导出 ranger 并迁移旧收据；真实 DNF TUI 启动/退出通过。
- 全局成功缓存会阻止上述入口修复。共享后端现在每次检查自身收据和链接，复用已有构建；
  原生/历史 hook 缓存仍保持兼容。
- PTY 启动失败曾让 fork 子进程展开父级临时目录的清理；改为明确退出 127，失败不影响后续用例。
  终端能力查询有响应，按键等待界面就绪，insect 使用输入前/后的不同标记。
- Mac Homebrew hook 失败时会退出整个 Shell 并改动 errexit/RETURN trap。
  改为条件捕获输出、保留 Shell 状态并返回原错误码，五项 Linux 模拟回归通过。

## 版本 GC

[managed_gc.py](scripts/managed_gc.py) 默认仅预览，--apply 才删除。使用安装器相同的 per-app 事务锁，
保护 current、previous、本机锁、仓库锁以及所有 BIN 链接。--keep 默认额外保留一个未引用版本。
只处理直接子目录且有匹配 backend/version 收据的版本；损坏状态/收据与软链锁拒绝处理。
不处理未知目录、Rust SDK、源码下载缓存或用户数据。

真实 ImageMagick/ccat 预览及 --apply 均保留受引用版本，没有删除候选。
独立临时三版本前缀实际预览后删除 v1，保留 previous v2/current v3；
五项 GC 回归还覆盖仓库锁、其他命令链接、外部目录、用户数据和损坏状态。
证据：[gc-results.json](validation/2026-10-15/gc-results.json)、[gc-fixture.json](validation/2026-10-15/gc-fixture.json)。

## 原生包离线恢复

[native_bundle.py](scripts/native_bundle.py) 保存 jq/tree/tmux 的精确版本与依赖闭包，
记录发行版 ID、版本和架构；拒绝平台不匹配、损坏、路径逃逸、软链资产和非法根包。
默认恢复只预览，--apply 才修改接收环境。

Ubuntu 保存 18 个 deb，以已验签 APT 索引的 SHA256 匹配下载；断网恢复通过 dpkg unpack/configure。
首次 apt-get 本地闭包恢复遇到 libsystemd 文件路径错误，没有将该失败记为成功。
CentOS 保存 48 个 RPM，创建时用 donor 信任库检查发布者签名；同时保存公钥和本地 repo 元数据。
接收端 DNF 关闭所有外部 repo，启用包签名校验，仅请求精确根包，复用已有依赖 provider。
没有使用 --allowerasing，保留最小镜像原有 coreutils-single；首次把整个闭包都列为请求的冲突已修复。

两个接收容器 network=none、Mounts=[]，实际恢复后再次核对根包版本，均通过。
Ubuntu 根版本为 jq 1.7.1-3ubuntu0.24.04.2、tree 2.1.1-2ubuntu3.24.04.2、tmux 3.4-1ubuntu0.1；
CentOS 根版本及完整清单见 [offline-restore.json](validation/2026-10-15/offline-restore.json)。
验证结束后两个具名离线恢复容器已停止，数据保留；既有 VM 和镜像保留供复查。

清单 SHA256 检测运输损坏，不能认证被整体替换的清单和公钥，因此 bundle 必须来自可信 donor。
这次只验证三个根包的保存/恢复，没有归档全部发行版库存，也不能保证包管理器独立的服务/用户数据已备份。

## 生成锁与 macOS 后续

software.lock.json 从 Ubuntu 42 个真实记录与 CentOS 缺失项合并生成，共 65 项。
export_lock.py --merge 校验来源并仅补缺失，本机收据优先；没有手改生成物。
lazygit v0.66.1 在 Ubuntu ARM 实际构建和 PTY 运行通过，作为独立可选工具，grv 的 ARM 限制保留。

[MACOS_TESTING.md](MACOS_TESTING.md) 说明无宿主污染的测试分层。
仅手动触发的 [macos-cli.yml](.github/workflows/macos-cli.yml) 已通过 Linux 中 YAML/脚本语法检查，
但未推送/执行；不使用本机 self-hosted runner。
真实系统配置、Homebrew/GUI/输入法兼容性仍需可销毁 macOS guest。
本轮未安装 Tart/UTM、下载 macOS 镜像、修改宿主默认设置或执行项目 macOS 脚本。
所有修改留在当前工作树，没有提交或推送。
