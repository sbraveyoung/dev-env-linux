# 安装幂等与已有 App 保护验证

2026-10-23。在无宿主共享目录的三个既有 Orb VM 中验证；Mac 宿主仅编辑、打包和传输源码。

| 隔离环境 | 命令 | 结果 |
| --- | --- | --- |
| Ubuntu 24.04 ARM64 / dev-env-verify-20261013 | bash scripts/check.sh | 121 回归、31 Shell 语法、ShellCheck 通过，退出 0 |
| Fedora 44 ARM64 / dev-env-fedora-20261014 | bash scripts/check.sh | 同上，退出 0 |
| CentOS Stream10 ARM64 / dev-env-centos10-20261014 | bash scripts/check.sh | 同上，退出 0 |

`*-check.txt` 是完整输出；`*-tools.txt` 记录 ShellCheck 版本和 guest 架构。
`source-sha256.json` 是宿主编辑的 86 个源码/配置/测试/锁文件摘要；
每个 VM 的 `*-source-check.json` 均确认 86 个文件一致，mismatches 为空。
不会用另一目录下的旧文件冒充此次验证。

新增 23 项回归位于 tests/test_install_idempotency.py：
已有手动/Brew App 跳过配置与缓存，直接 hook 不下载，缺少 Brew 时不引导安装，
用户 Applications、按 ID 改名、损坏包/同名不同 ID、已有 Qt 及所属链接边界、
WeType 输入法和过期缓存、检测错误与严格声明、Brew 未验证冲突仍失败、
dotfiles 重复安装保留内容/时间戳/快照、Alacritty 用户配置、Go 用户命令/目录/链接保护。

失败先行验证在隔离 Ubuntu 中观察到原问题，再实施修正；
只读复核另发现 Go 真实 SDK 目录的命令链接保护与 WeType 缓存遗漏，
各自新增回归确认失败后修复，随后三个 VM 全部复验通过。

`cask-reference.json` 为核对 App artifact 的官方 Homebrew API 只读参考快照，
不参与运行或测试预期值；其中 quit 可能包含 helper，不能直接当作主程序 ID。
真实维护源是 config/software.json。

这里的 macOS 包、brew、Qt 外部工具是 Linux 内的临时替身，验证的是检测和文件保护逻辑。
本轮未执行真实 macOS GUI/Homebrew/输入法安装、签名或授权测试，未重新全量实装默认工具。
各渠道实际保证与限制见 ../../INSTALLATION_SAFETY.md。
