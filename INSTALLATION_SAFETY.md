# 重复安装与已有软件

不能把所有入口都称为“严格幂等”或“不会改变系统”。首次安装会按所选渠道安装依赖、写配置，
重复安装也可能修复链接、写收据，或重新执行系统设置。成功缓存只是执行记录，不是系统快照。

| 入口 | 重复 install 行为 | 仍可能改变的状态 |
| --- | --- | --- |
| Go/Cargo/pip/npm/Git/源码共享后端 | 同一来源与版本复用收据和版本目录，修复所属命令入口；拒绝覆盖非所属入口 | 私有收据、锁和链接可能重写；首次缺依赖会调用系统包管理器。声明的期望版本改变、收据迁移或版本缺失可能需要构建 |
| APT/DNF 原生包 | 包管理器处理已安装包；未必固定原版本，成功缓存通常跳过已成功 hook | 清缓存、调整参数或显式重跑可能安装新候选版本及依赖；不是零系统变更 |
| macOS Homebrew | 安装前先查已有 App，再查 brew list；命中则跳过整个安装和配置流程；安装 hook 不依赖旧成功缓存 | 尚未安装时才按需引导 Homebrew、tap、安装软件；依赖由 Homebrew 处理 |
| macOS Qt 源码 App | 已有外部 App 时跳过 install；所属 App 使用私有版本与收据，复用构建并修复链接 | 所属 App 链接和收据可重写；缺失版本需构建，依赖由 Homebrew 安装 |
| macOS WeType | 检测到 Input Methods 中已有完整 WeType.app 时跳过下载与配置 | 尚未安装时只准备版本化的 WeTypeInstaller；输入法启用、系统授权不等于已自动完成 |
| 仓库 dotfiles / this-repo | 独占锁下先处理未完成事务；已有收据时 install 保留修改 | 显式 upgrade 应用仓库内容；正常错误尝试回滚，进程中断由下次 dotfiles 调用恢复；冲突保留文件并停止 |
| Go SDK | 复用请求版本的私有 SDK；拒绝覆盖用户命令和非所属 SDK 链接；没有所属 SDK 链接时卸载保留用户入口 | 修复所属链接；旧的私有未版本化目录可能迁移为保留备份；安装新版本仍需下载 |
| Rust SDK | 使用私有 RUSTUP_HOME/CARGO_HOME，保留用户 ~/.rustup 与 ~/.cargo；拒绝覆盖非所属命令 | 失去全局缓存或直接调用可重新运行 rustup、重写私有 wrapper；upgrade 会更新私有工具链 |
| 旧的可手动选择 hook，如 htop、SDL、pomo | 主要依赖成功缓存，不保证直接调用或清缓存后的严格幂等 | 可重新构建、重建链接；部分历史 hook 向系统前缀安装。应只在一次性环境选择 |
| 系统初始化 | 一些步骤有成功缓存；设置为同一值并不代表保留用户后来改过的偏好 | Linux 源、全系统包升级、时区、SSH 权限；macOS defaults（触控板/Dock 等）仍可能写入 |
| Docker 包装入口 | 会构建镜像；同名容器存在时返回错误，不自动删除容器 | 镜像可更新，不是重复执行成功的幂等入口 |
| Orb VM 包装入口 | 复用同名 VM，传输完整源码与版本锁；仅更新所属且未改过的文件 | guest 编辑或未知同名文件不同于投递内容时整批源码同步拒绝；缺 Python 时先在 Ubuntu guest 引导；显式密码参数可重设 guest 密码 |

## macOS 手动 App 的处理

扫描 `/Applications`、`~/Applications` 及下一层目录，包含用户目录安装和常见 Utilities 目录。
额外路径、App 名称和可选 bundle ID 在 `config/software.json` 中维护。
有 ID 时按 ID 精确匹配，可识别改名的 App；没有 ID 时按声明的 App 文件名匹配。
候选必须包含可解析 Info.plist、APPL 类型、非空 bundle ID 和包内存在且可执行的主程序。
空目录、损坏包、断链不被当作成功安装；读取权限或无效声明等检测错误会停止后续安装。

命中已有 App 后，在 preinstall、下载、tap、Homebrew 引导、配置和缓存写入之前返回。
因此不会因重复 install 再设置 Chrome 默认浏览器、重装字体或重写所选 App 配置。
不创建接管收据；Qt 的 upgrade/uninstall/rollback 拒绝操作外部 App，Homebrew 操作仅限 brew list 确认的包。
安装冲突只有经过正向检测才跳过，其他 Homebrew 错误原样失败，不再靠错误文本报告成功。

检测不执行已有 App，不读取密码或启动它们，也不移除用户的软件。
这不是签名认证或版本兼容性检查：已有版本即使比清单中的目标版本旧，install 仍保留它。
外部 App 的更新由用户原有安装渠道管理。Homebrew 的状态检查基于其包记录，不是完整文件校验。

检测范围有边界：任意自定义目录、尚未声明的历史名称/ID、任意手动安装的 CLI，以及多个不同发行版的
同类产品，不能靠名称可靠推断。需要时先在清单补全准确声明或额外目录。
不扫描整个磁盘或 Spotlight，以免把下载副本、挂载安装镜像当作已安装软件。

## 使用边界

已有依赖的隔离 guest 中可使用 `--skip-system --only=APP` 缩小范围。
`--skip-system` 只跳过 OS 初始化，不禁止所选安装器安装依赖或首次生成 App 配置。
需要更新受管理内容时显式使用 `--operator=upgrade`；dotfiles 升级会应用仓库配置，先确认这是你的意图。
`--clean_cache` 只删除成功缓存，不还原已安装的软件、依赖或系统设置。

本项目仍只在隔离 VM/容器运行安装与测试。当前 Mac 宿主没有执行这些功能。
Linux 内的 App 包、Homebrew 和 Qt 外部工具替身用于验证控制流与文件保护；
不能据此宣称已完成真实 macOS 的 Homebrew、GUI、输入法授权或代码签名验证。
真实 macOS 隔离方案见 [MACOS_TESTING.md](MACOS_TESTING.md)。

本轮检查证据见 [validation/install-idempotency](validation/install-idempotency)。

## 2026-10-27：事务恢复与 guest 源码保护

VM receiver 的清单 `.dev-env-source-manifest.json` 记录源码内容及权限；更新与删除先整批检查。
额外笔记保留，冲突阻止构建。相同源码可以在中断后重试，但源码同步不是整批原子发布。
不应在同步期间同时编辑 guest 中同一批文件；安装器的锁只协调安装器进程。

Dotfiles 使用事务锁、原子 JSON 收据、`pending.json` 与同目录临时旁路文件。
支持独立的 `python3 scripts/dotfiles.py recover`，仅在 guest 中执行；通常下次 dotfiles 生命周期自动处理。
它区分“收据已提交，只需清理”和“未提交，恢复原状”；用户中断后新增编辑则停止，保留恢复依据。
新收据记录权限与目录结构状态，目录 symlink 不跟随其目标；原本不存在且未被再修改的 `.bashrc` 在卸载时移除。
旧收据仍兼容内容比较，但无法追溯以前没有记录的权限变化。
这些保证针对进程中断，不声称整机断电或磁盘损坏下的完整持久事务。
证据见 [validation/safe-workflows](validation/safe-workflows)，新手解释见 [BEGINNER_GUIDE.md](BEGINNER_GUIDE.md)。
