# TODO 补齐验证

2026-10-15，原目录开发；宿主仅编辑、封装及传输文件，没有原生运行项目安装或测试。

- Ubuntu 24.04 ARM64、Fedora 44 ARM64、CentOS Stream 10 ARM64：各 97 项测试、31 个 Shell 文件语法检查、ShellCheck 通过，完整输出为对应 *-checks.txt。
- 新增 18 项测试（79 → 97），覆盖备份/恢复、日志、目录环境卸载、SSH 配置部署/迁移、编辑器配置保护、Qt 安装生命周期与失败隔离、显式 Homebrew tap 和收据缓存。
- source-sha256.json 及三个 *-source-match.json 核对当轮 84 个被测文件。后续提交前修正与最终快照见 ../precommit。
- Ubuntu VM 内真实编译 H264Naked、FlvParser、YUView 固定源码，并以临时 HOME、QT_QPA_PLATFORM=offscreen 启动各 3 秒；进程保持运行至测试超时，由测试结束。
- upstream-build-smoke.json 包含官方提交、可执行路径和启动结果；todo-*-build*.log 保存编译原始输出，包括修复前的资源路径/缺少 Qt OpenGL 依赖错误。
- H264 库的 2012 配置探测不支持 ARM64，经 autoreconf 从 configure.ac 重新生成；日志 todo-h264-autoreconf.log / todo-h264-library.log。
- 源码编译保留上游旧代码的编译警告，离屏插件有 propagateSizeHints 提示；这里只证明该 Linux 构建与启动路径，不证明 GUI 交互、媒体解析准确性或 macOS 签名/打包/授权已认证。
- macOS 构建调度、macdeployqt 调用及应用链接保护使用 Linux 中的外部命令替身测试。未运行真实 macOS 构建/安装，也没有运行商业软件激活。
- YuvEye 和 StreamEye 仍缺必要来源/安装包信息，没有伪装安装成功；逐项状态见 ../../TODO_STATUS.md。
