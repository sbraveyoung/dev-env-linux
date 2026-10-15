# 开发约定

以后在当前 `dev-env-linux` 仓库根目录开发。上层的 `dev-env-linux_bak` 和
`dev-env-linux.claude.bak` 已合并后于 2026-10-13 按用户要求删除，不作为后续开发目录。
合并来源与冲突处理见 [MERGE_NOTES.md](MERGE_NOTES.md)，项目说明见 [CLAUDE.md](CLAUDE.md)。

- 生成文件应修改生成源，避免直接修改会被 generate/build 覆盖的产物。
  遇到修改反复消失，先检查是谁重新生成了文件。
- 工具能完成的修改、编译、验证及部署由 agent 自行完成；只有需要用户判断、
  密钥或无法代操作的系统/硬件交互才找用户，并明确原因及完整步骤。
- 使用 sub agent/team mode 时，每个 agent 的功能必须由用户逐个独立验收；
  用户确认 OK 后才能关闭该 agent，不可自行完成验收或打包验收。

改动验证在 Orb VM 内执行 `bash scripts/check.sh`；不得在 Mac 原生运行。优化推进计划见
[OPTIMIZATION_PLAN.md](OPTIMIZATION_PLAN.md)。

## 隔离执行（用户要求）

不得在 Mac 宿主机原生执行项目构建、安装脚本或测试。仅在隔离的 Orb VM/容器中运行。
宿主机仅用于编辑源码、检查文件与调用 Orb/Docker 管理命令。当前验证 VM 为
`dev-env-verify-20261013`（Ubuntu 24.04 ARM64，`--isolated`，无宿主共享目录）。

2026-10-14 扩展验证环境为 Fedora 44 与 CentOS Stream10（均 `--isolated`）。
完整结果见 [FULL_VALIDATION.md](FULL_VALIDATION.md)。维护共享安装来源时改
`config/software.json`/安装器；软件分组、包映射、默认版本和来源只在该声明中维护。
读取/校验接口是 `scripts/catalog.py`，维护方法见 `SOFTWARE_CATALOG.md`；
`software.lock.json` 使用 VM 中 `scripts/export_lock.py`
重新生成。Dockerfile、兼容层模板是生成源；不要手改容器中的生成物。
内部旧目录在忽略的 `archive/legacy/`，本地运行日志在 `.local/history/`，不作为活动源码。
