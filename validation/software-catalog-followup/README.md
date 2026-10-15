# 软件声明统一校验验收

2026-10-15，续接软件声明提取工作。

- Ubuntu 24.04 ARM64、Fedora 44 ARM64、CentOS Stream 10 ARM64：各 79 项测试、31 个 Shell 文件语法及 ShellCheck 通过。完整日志为对应 *-checks.txt。
- 新增 6 个测试方法，覆盖 17 种嵌套错误、五个直接 Python 入口、临时清单选择、Darwin 分组兼容性及版本展示。Ubuntu 修复前观察到 26 个失败子项，修复后完整测试通过。
- 五个消费者统一使用 scripts/catalog.py 校验读取，无效声明在写入安装/清理状态、创建批量结果目录和读取收据前失败。
- dev-env-catalog-followup-ubuntu 使用已有本地 Ubuntu 镜像，复制本轮完整源码，在普通用户 HOME 内运行 79 项测试；无网络、无宿主目录挂载，退出码 0。不是本轮 Dockerfile 冷构建。
- 容器首次解包到 Docker 创建的 root 所有目录失败；改为普通用户 HOME 后通过。container-preparation-error.txt 保留原始错误，container-state.txt 记录最终退出码及隔离设置。
- source-sha256.json 是本轮被验证代码与配置的指纹，*-source-match.json 核对 VM 和容器中的文件。
- 默认软件清单和 software.lock.json 未改动；此轮未重装全部 76 项软件。原来的完整安装验证见 ../software-catalog。
- macOS 仍仅 Linux 模拟测试，未进行真实 macOS 安装；Mac 宿主只编辑、读写验证产物及管理隔离环境。

配置维护说明见 [SOFTWARE_CATALOG.md](../../SOFTWARE_CATALOG.md)。
