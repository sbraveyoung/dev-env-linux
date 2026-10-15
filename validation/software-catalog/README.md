# 软件声明提取验收

- Ubuntu 24.04 ARM64、Fedora 44 ARM64、CentOS Stream10 ARM64：各 73 回归、31 Shell 语法及 ShellCheck 通过。
- 三个 VM 默认 76 应用队列复验全部通过；复用已验证的安装版本，未再次从零下载全部工具。
- linux-default-before.json 是迁移前的一次性基线；新声明与之保持同一 76 项及顺序。
  它不参与永久测试，后续调整声明无需更新另一份运行清单。
- declared-version-lifecycle.json：在隔离 Ubuntu 的独立 APP_PATH/BIN_PATH 中，声明 ccat v1.0.0 安装、
  声明改为 v1.1.0 升级、再显式回滚 v1.0.0，原命令运行通过；仓库生成锁未改动。
- 两个断网、无宿主挂载容器各通过最终 73 回归。CentOS Dockerfile 最终构建通过。
  Ubuntu Dockerfile 本轮首次构建通过；最后重建遇到 Docker Hub 对 ubuntu:24.04 返回 not found，日志保留。
  最终 Ubuntu 验证复用本轮本地已构建镜像，复制最终配置/测试，源码指纹核对一致，容器退出码 0。
- source-sha256.json / ubuntu-source-match.txt 保存最终验证快照的源文件指纹核对。
- macOS 仍仅 Linux mock 验证；没有运行真实 macOS 安装，没有宿主原生项目执行。

配置维护方法见 [SOFTWARE_CATALOG.md](../../SOFTWARE_CATALOG.md)。
