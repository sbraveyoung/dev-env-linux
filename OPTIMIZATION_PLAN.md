# 仓库优化推进计划

2026-10-13。目标：把现有 macOS/Linux 开发环境脚本变成可验证、可重跑、失败可诊断的工具。
当前在原目录就地优化，保留已合并的改动与软件选择，不重写技术栈。

## 第一批：执行可靠性（已完成）

| 任务 | 文件 | 验收 |
| --- | --- | --- |
| 修复缓存与参数传递 | scripts/common_defines.sh | 缓存精确匹配；参数含空格保持原样；失败不写入缓存；保留简单旧缓存 |
| 修复并发与失败汇总 | sheath/functions.sh、common_defines.sh | 子任务失败不会挂死或误报成功；并发上限有效；空队列成功；非法并发立即失败 |
| 保留源码与 caller 环境 | 两平台 apps 脚本、common_defines.sh | 安装退出不删除 CLONE_PATH；从任意 cwd 加载 common_defines 不切换 cwd |
| 校正入口 | build.sh、scripts/cli.sh | --help 无安装副作用；从任意目录调用正确定位；非法 operator/并发/参数立即失败；app flag 保留 = 和空格 |
| 建立回归验证 | tests/、scripts/check.sh | 单一检查命令；隔离临时目录；模拟包管理器，无宿主安装；含原故障回归 |

已完成：21 项回归通过，35 个 Shell 文件语法检查通过；使用 `bash scripts/check.sh` 复验。
执行顺序：为每项先运行失败测试 → 最小修复 → 全套回归 → 更新文档。
最初第一批只做模拟验证；续作已获用户授权在隔离 Orb VM 内真实安装。
不在 Mac 原生执行项目，不自动提交/推送。

## 第二批：发行版与平台支持（关键修复已实施，Ubuntu ARM64 已实测）

- 把 dive、ffmpeg、iredis 中直接引用 RPM/DNF 的代码迁入驱动接口，分别验证 APT/DNF。
- 将架构探测及下载 artifact 映射统一管理，支持 amd64/arm64；无官方 artifact 的应用明确报错。
- 校正 DNF 的 Fedora/RHEL/CentOS 仓库分支与 APT 的 Debian/Ubuntu PPA 分支。
- 优先验证最小应用集合，再扩大软件清单，避免把抽象存在误当成已支持全平台。
- 验收：隔离容器里的安装/升级/卸载矩阵，而非仅 bash -n。

## 第三批：可重复安装与运维（执行与缓存修复已实施）

- 真正实施 TIMEOUT；定义取消时对子进程与下载文件的清理规则。
- 版本查询增加总超时、严格版本格式校验；使用可信下载校验和。
- 缓存记录版本、平台、操作及成功时间，支持按应用刷新，避免升级永远命中旧缓存。
- 将 install/upgrade/uninstall 按包管理器提供一致能力，并区分不可用操作。
- 验收：离线、限流、下载中断、升级版本变化、失败重试场景。

## 第四批：容器与维护入口（入口与 Dockerfile 已重建）

- 修复 Docker COPY/构建上下文，并复用 build.sh，减少 Ubuntu Dockerfile 与原生脚本的重复知识。
- VM/Docker 统一转发 enable/disable 与 app flags，修正密码设置机制。
- 整理源码、旧的 linux/ 配置、内部 *.bak 及本机状态文件；确认引用后再归档，避免误删。
- 接入 CI：Bash 语法、回归测试、分阶段 ShellCheck、Linux 容器烟测；macOS 原生测试不在本次授权范围。
- 文档统一以真实 CLI 和测试命令为准。

## 取舍

优先最小、可测试的修复。软件清单的删除/替换、操作系统配置策略、容器发行版迁移
需要单独验证，作为后续批次执行。本次分析的风险证据见 TECH_DEBT.md。

## 2026-10-13 续作结果

- 修复 Shell 引用/局部变量、smart_cp 嵌套目录、环境值恢复的 eval、save_env 精确匹配、PATH 覆盖和缺失可选集成。
- 安装目录默认改为用户私有的 ~/.local 目录，仍支持环境变量覆盖；修复历史 sudo 创建的用户目录权限。
- 下载写入临时文件，成功后替换；网络请求有连接/总超时，Go 使用 ARM64/AMD64 映射及版本化目录。
- APT 不再使用 ARM 上不存在的包或向 Debian 添加 Ubuntu PPA；原生包有 upgrade/uninstall 接口，包事务串行。
- --only/--skip-system 支持选择性验证；虚拟机和容器完整转发 argv，密码通过 stdin 设置，不开启 xtrace。
- TIMEOUT 真正生效，杀掉任务进程组后返回 124；升级不命中旧缓存，卸载后失效安装缓存。
- Ubuntu 24.04 ARM64 隔离 VM：34 项回归、ShellCheck、真实包生命周期、Go 1.27.2、Shell 配置全部通过。

## 明确保留的后续验证

- 软件清单中的每一个第三方工具并未逐项安装；无 ARM 下载资产的工具明确失败。
- DNF/Fedora/EL 与 macOS 安装没有真实执行，不以静态检查代替兼容性认证。
- 全部下载资产的校验和、通用版本缓存结构、CI、历史 linux/ 与内部 .bak 归档仍为后续任务。
- Orb VM 在本次验证后保留，详细证据见 ORB_VALIDATION.md；Docker 验证结果在那里独立记录。

Ubuntu 镜像实际构建通过，最终容器真实 jq/tree 安装与重复执行通过；VM/容器均通过 34 回归。详细隔离证据与未覆盖范围见 ORB_VALIDATION.md。

## 2026-10-14：用户授权的五项扩展（已完成）

1. 默认 76 个工具在 Ubuntu ARM64 全量实装；修复失败并逐项重测。
2. Go/Cargo/Python/npm/Git/源码共用版本目录、升级卸载和安全链接；SDK 与 dotfiles 单独管理。
3. Fedora44 与 CentOS Stream10 基础依赖、DNF 生命周期与部分共享后端实测。
4. 官方 SHA256、渠道校验、41 项生成版本锁、空白前缀重建与真实版本回滚。
5. 固定提交的 CI、Docker 构建验证、内部旧目录和本地运行文件完整归档。

具体证据与保留限制见 [FULL_VALIDATION.md](FULL_VALIDATION.md)。暂不自动清除可回滚版本，
不恢复已停用的 forgit 下载；grv ARM 上明确不支持。后续可按需要增加 TUI 交互验收和其他发行版的全应用组合矩阵。

## 2026-10-15：剩余维护项（已完成）

1. Fedora/CentOS 各 76/76 默认工具实装及整队复验，修复 axel 源码回退与 broot 低内存构建。
2. 显式 GC 预览/删除，保护当前、回滚、锁、链接及未知数据；真实临时前缀删除验收。
3. 代表原生包闭包保存、校验和断网精确恢复，Ubuntu 18 deb/CentOS 48 RPM，不强制擦除依赖 provider。
4. Ubuntu 16/Fedora 15/CentOS 15 项真实 TUI 按键烟测，修复 ranger 入口、旧成功缓存和测试器问题；lazygit ARM 实装。
5. 三 VM 与两容器各通过 61 回归；30 Shell 语法通过，VM ShellCheck 通过；生成锁更新至 65 项。

见 [MAINTENANCE_VALIDATION.md](MAINTENANCE_VALIDATION.md)。macOS 真实验收独立保留：
已补 Linux 模拟回归、修复安装 hook，准备仅手动远端 CI；尚未发布/触发、未在宿主执行。
方案见 [MACOS_TESTING.md](MACOS_TESTING.md)。GUI/系统设置需独立 macOS guest。
