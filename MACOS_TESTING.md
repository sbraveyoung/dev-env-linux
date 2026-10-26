# macOS 功能的隔离验证

宿主 Mac 不运行 build.sh、安装脚本或测试，不安装 Homebrew/虚拟化工具，不改系统设置。
当前仅完成 Linux 内模拟测试；尚未创建 macOS VM，也未触发远端 macOS CI。

## 当前已做：Linux 中模拟 Homebrew

在已有隔离 Orb/Linux 内运行 `bash scripts/check.sh`，其中
[test_macos_mock.py](tests/test_macos_mock.py) 使用临时 HOME 和假 brew，验证已安装软件的升级/卸载、
缺失软件的跳过、重复安装，以及失败返回和调用者 Shell 状态的保留。它不会安装 Homebrew，
也不会执行 defaults、open 或 /Applications 写入。

这种测试能发现编排问题，不能证明 Homebrew、Darwin 或 GUI 的实际兼容性。

## 宿主不新增测试环境：远程临时 Mac

建议先使用 GitHub 托管 macOS runner 验证命令行软件。每个普通托管 job 使用新 VM，
无需把当前电脑注册为 self-hosted runner。依据：[GitHub runner 文档](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)。

[macos-cli.yml](.github/workflows/macos-cli.yml) 已准备为仅手动触发的工作流：
macos-15 guest 内安装 Bash 4+，真实执行 tmux 安装、重复安装、升级、卸载、重装并保留日志。
所有项目调用使用 --skip-system；它不测试 GUI 或系统配置。本地准备不等于执行成功，
本轮没有提交、推送或远端触发。

应用启动、触摸板/Dock、默认浏览器和输入法等需要可交互的远程 macOS guest，再逐项验收。
测试机使用空白测试账号，不登录个人 Apple ID，不导入钥匙串、SSH agent、用户目录或真实凭据。
先保留干净快照，每批测试后恢复，结束后销毁。

## 允许临时磁盘占用时：本机独立 macOS VM

Tart 或 UTM 可用于支持的 Apple Silicon 主机；先确认具体主机/系统要求。
参考：[Tart quick start](https://tart.run/quick-start/)、[UTM macOS guest](https://docs.getutm.app/guest-support/macos/)。
VM 本身仍会占用宿主磁盘、CPU 和内存，因此它不符合“宿主不新增任何测试环境文件”的要求。
本轮未安装这两种工具或下载镜像；是否采用本机 VM 仍待选择。

使用时关闭共享目录、剪贴板、拖放和凭据转发，仅复制筛选过的源码归档到 guest；
不包含 test.sh、archive/、.local/、.git/ 或本机密钥。不要把宿主代码目录以可写方式挂入 guest。
在 guest 中安装依赖并建立快照，之后运行项目；不要在宿主终端运行 macOS 安装命令。
真实 GUI 验收需要明确记录 guest 版本、架构、安装状态、启动结果和还原结果。

## 系统配置需要单独测试

[setup_macos_system.sh](scripts/setup_macos_system.sh) 当前会修改触摸板/Dock，
并准备安装目录；已移除关闭 LSQuarantine、跳过 DMG 验证和目录全员可写的旧行为。
Mac app hooks 还可能写 /Applications、修改默认浏览器与 shell 配置。
更换 HOME 或创建一个本机测试账号无法隔离全部系统级改动。
这部分只在可销毁 macOS guest 中测试，不能以容器或 Linux mock 替代。

## TODO 补齐后的验证边界

新增 tests/test_macos_todos.py 覆盖 He3 官方 tap、未选分组的 --only/--enable 钩子、VS Code/kitty 用户文件保护、
固定提交 Qt 应用的安装/升级/回滚/卸载、失败不发布、旧成功缓存不能跳过收据等行为。
全部在隔离 Linux 中执行，Git/Qt/Homebrew/macdeployqt 使用外部工具替身。
H264Naked、FlvParser、YUView 的真实官方源码另在 Ubuntu ARM64 编译并离屏启动；不据此宣称 macOS App 打包、签名或 GUI 已真实验证。
记录见 validation/todo-completion，来源阻塞项目见 TODO_STATUS.md。

提交前最终修正见 validation/precommit：初始化保留系统下载隔离和镜像验证，安装目录不再设置为所有人可写。
该行为通过 Linux 中 defaults/sudo 替身回归验证，未在用户 Mac 原生执行系统设置。
