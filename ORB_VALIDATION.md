# 隔离验证记录

执行日期：2026-10-13 至 2026-10-14。所有真实安装与续作最终测试均在 Orb 的 Linux VM/容器中执行。
Mac 宿主机只做源码编辑、文件传输与 Orb/Docker 管理；未进行原生系统安装。
用户要求的隔离执行约束已写入 AGENTS.md。

## 环境

| 环境 | 标识 | 隔离/状态 |
| --- | --- | --- |
| Orb VM | dev-env-verify-20261013 | Ubuntu 24.04 ARM64，创建使用 --isolated，无宿主文件共享，2 CPUs / 4G 内存 / 32G 磁盘上限 |
| Docker 镜像 | dev-env-linux-verify:20261013 | OrbStack Linux ARM64 引擎构建，Ubuntu 24.04 |
| 最终验证容器 | dev-env-container-verify-final-20261013 | developer 普通用户，Mounts=[]，未挂载宿主目录，保留运行 |

VM 中的源码路径：`/home/sbrave/dev-env-linux`。
容器中的源码路径：`/opt/dev-env-linux`。
源码通过归档标准输入复制，不与宿主工作区共享可写挂载。

## 修复与失败复现

1. 全局目录退出清理、队列失败状态、参数拆分和不精确缓存：由首批回归约束。
2. ShellCheck 揭示大量未引用的路径、非局部变量和动态求值；修复 smart_cp/备份/环境恢复/日志/参数转发。
3. 用户值恢复的 eval 会再次解释 Shell 文本：改为间接引用和 printf -v，验证字面值不执行。
4. save_env 在 errexit 下重复/缺失值退出或正则误判：改为精确整行匹配和正常返回。
5. ~/.local/bin 被旧 sudo mkdir 创建为 root 所有，真实 Go 安装不能链接：修复用户目录所有权及默认用户私有路径。
6. 真正卸载 tree 后重装被旧缓存跳过：卸载成功失效 install/preinstall/config 记录；upgrade/uninstall 不命中安装缓存。
7. 固定 amd64 的 Go/RPM 下载：Go 与 dive 使用架构映射，dive 使用驱动提供的 deb/rpm 格式；未配置 ARM 资产的工具显式失败。
8. Go 请求版本变化会复用旧 archive：版本化 archive 与安装目录，并按实际版本/架构失效成功缓存。
9. wget 中断留下文件被当成成功下载：临时文件下载，成功才重命名，失败清理；查询与下载加超时。
10. 超时参数无执行机制：应用级进程组 watchdog，超时清理子进程并返回 124；回归验证成功及超时分支。
11. APT 并发锁、缺失 ARM 包、Debian 的 Ubuntu PPA、系统 pip：串行包事务，校正包名，移除无用 PPA，pipx/独立 venv。
12. Docker WORKDIR root 所有导致成功缓存不可写：修改 Dockerfile 生成源 chown 并重建；最小镜像还验证了 ssh-keygen 的按需依赖安装。
13. 部分安装后交互 cat 指向不存在的 bat：真实 bash -ic 复现，所有可选替代工具仅在存在时启用。
14. VM/Docker 参数丢失、密码命令错误、xtrace：统一数组 argv 转发、stdin chpasswd、关闭默认 xtrace。

## 验证结果

| 检查 | 结果 | 范围 |
| --- | --- | --- |
| VM 回归测试 | PASS，34 项 | 公共执行、CLI、缓存、超时、下载、环境工具、可选别名 |
| 容器回归测试 | PASS，34 项 | 同一最终源码副本，普通用户执行 |
| Shell 语法 | PASS，28 文件 | 复制的活跃源码与测试脚本；历史内部备份不在 VM 副本 |
| ShellCheck | PASS，warning/error | 活跃 build/scripts/sheath/config relay/smoke；SC2034 跨模块全局及 SC1090 动态 source 为明确静态限制，单行别名捕获有意行为有注释 |
| VM 初次安装 | PASS | jq、tree、ripgrep、tmux，包含系统初始化 |
| VM 重复安装 | PASS | 成功记录精确命中 |
| VM 升级 | PASS | tree；确实调用 apt --only-upgrade，未被旧缓存跳过 |
| VM 卸载后重装 | PASS | tree；真实移除后成功重新安装 |
| VM Go | PASS | go version go1.27.2 linux/arm64，下载与链接实际执行 |
| VM Shell 配置 | PASS | sheath/init.sh，PATH，.bashrc 单条集成，重复部署不追加 |
| VM 交互 Shell | PASS | cat /etc/hostname 在缺失 bat 时正常运行 |
| Ubuntu 镜像构建 | PASS | 实际 docker build 成功 |
| 容器实际安装 | PASS | jq、tree，用户/缓存/SSH 初始化权限正常 |
| 容器重复安装 | PASS | 对应成功缓存正常命中，jq 二进制输出 jq-1.7 |
| 容器隔离核对 | PASS | developer [] true，Mounts 为空 |
| Git 差异格式 | PASS | git diff --check |

VM 原始日志保存在 `/home/sbrave/dev-env-validation-results/`，包括
check.log、install.log、repeat.log、upgrade.log、uninstall.log、reinstall.log、go-config.log、
go-version.txt、profile.log、tree-version.txt。

## 复验命令（宿主只调用 Orb/Docker）

```bash
orbctl run -m dev-env-verify-20261013 -w /home/sbrave/dev-env-linux bash scripts/check.sh
orbctl run -m dev-env-verify-20261013 -w /home/sbrave/dev-env-linux bash tests/orb_smoke.sh
docker exec dev-env-container-verify-final-20261013 bash scripts/check.sh
```

orb_smoke.sh 会在这台测试 VM 中安装/升级/卸载并重装测试软件，不能当作只读测试。

## 范围与后续事项

已修复本轮定位的 Shell 执行与平台问题，并完成上述真实验证。
没有逐项安装全量第三方软件，没有执行 macOS 原生安装、DNF/Fedora/EL 实装或 CentOS 镜像构建。
VM/Docker 调度层在 Linux 中有 argv 回归保护，但按用户约束未在 Mac 执行项目调度脚本。
下载资产的通用校验和、完整软件/发行版矩阵、CI、旧 linux/ 与内部 .bak 归档仍在推进计划中。
没有提交、推送或发布代码。源码原有本机文件和历史内部备份保留。

2026-10-14 的扩展验证（76 个默认工具、三发行版、41 个测试、源码与 SDK 生命周期、
版本锁重建及两个 Docker 镜像）见 [FULL_VALIDATION.md](FULL_VALIDATION.md)。
