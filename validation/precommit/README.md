# 提交前最终验证

2026-10-15，用户授权本地提交；不推送远端。

- 修正 macOS 初始化旧默认：保留系统隔离/镜像验证，不再 chmod a+w；用户目录使用普通权限创建，必要时修复当前用户目录所有权。
- 新增 Linux 工具替身回归，核实系统偏好仍可设置、安装目录确实创建且未关闭安全检查。
- Ubuntu 24.04、Fedora 44、CentOS Stream 10 的最终代码各通过 98 项测试、31 个 Shell 文件语法及 ShellCheck；日志为 *-checks.txt。
- 新测试首次在 Fedora/CentOS 失败，是测试继承了现有 GOPATH/APP_PATH，导致临时目录断言失败；测试已显式固定所有目录，再运行通过。原始失败记录保留为 *-before-fixture-fix.txt。
- source-sha256.json 与三个 *-source-match.json 记录 84 个源文件/配置及实际测试快照的一致性。
- 无宿主原生项目执行；未在真实 macOS 环境验证。YuvEye/StreamEye 来源阻塞保持 TODO_STATUS.md 中的明确状态。
