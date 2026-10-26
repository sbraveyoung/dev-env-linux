# 安全投递、配置事务与入门文档

2026-10-27。上轮幂等保护在提交 930e478 中单独保存。本轮所有项目执行都在隔离 Orb guest 内，Mac 宿主仅编辑、打包、Git 和调用 Orb。

| 环境 | 完整检查 | 源码摘要 |
| --- | --- | --- |
| Ubuntu 24.04 ARM64 / dev-env-verify-20261013 | 144 回归 + 31 Shell 语法 + ShellCheck，退出 0 | 89 文件一致 |
| Fedora 44 ARM64 / dev-env-fedora-20261014 | 同上，退出 0 | 89 文件一致 |
| CentOS Stream10 ARM64 / dev-env-centos10-20261014 | 同上，退出 0 | 89 文件一致 |

完整输出为 *-check.txt；静态检查工具版本为 *-tools.txt；source-sha256.json 和各 VM 的 *-source-check.json 确认受测源码一致。

本轮增加 23 项回归：tests/test_source_sync.py 8 项，tests/test_dotfile_transactions.py 15 项。
包含版本锁实际传输、guest 最初缺 Python 的引导编排、整批同步冲突检查、未知文件、模式/路径/删除保护、目录 symlink、
配置独占锁、准备和收据写入失败、SIGKILL 后恢复、收据提交后 SIGKILL 的清理、缓存不能跳过恢复、
startup 原文件缺失/权限恢复和用户后来收紧的权限保护。
核心故障均在隔离 Ubuntu 中先观察失败，再修正。最小 guest/Python 包管理器及 Orb 编排使用 Linux 外部工具替身，未真的新建或清除系统 Python。

ubuntu-source-delivery-smoke.json 另外在真实 Ubuntu guest 一次性目录投递整个源码归档：
89 文件、65 条仓库锁记录，重复投递保留 guest 笔记；修改 build.sh 后整批同步返回冲突，原文件及清单不被重写；
投递后的 build.sh --help 成功。临时目录在退出时清理。

Dotfiles 回归使用真实临时文件、权限、符号链接、进程锁和 SIGKILL；没有使用真实日常 HOME。
验证对象是进程中断后的保守恢复，不扩展为断电/坏盘持久性保证，也不对抗同用户恶意并发替换目录。
源码接收不是整批原子切换；中断可用相同投递重试，冲突不自动覆盖。

只读代码复核发现并修正：首次 guest 缺 Python 的引导顺序、目录 symlink 指纹遗漏、卸载保留后续 chmod。
入门文档读者核对后修正了“相同文件可纳入投递”和显式固定版本优先级两处表述。
详细讲解见 ../../BEGINNER_GUIDE.md；保护边界见 ../../INSTALLATION_SAFETY.md。

本轮没有全量重装默认软件、运行真实 Mac 安装/GUI/签名/输入法授权或触发远端工作流。
没有手改生成版本锁，也没有推送远端。
