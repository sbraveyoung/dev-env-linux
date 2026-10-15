# 备份目录合并记录

合并日期：2026-10-13。以后在当前 `dev-env-linux` 仓库根目录开发。
`../dev-env-linux_bak` 和 `../dev-env-linux.claude.bak` 在合并验证后于同日按用户要求删除。
以下记录描述合并时的来源；合并前快照仍在下方列出的临时目录。
三份仓库基于同一提交 `6caefd5`，差异均来自未提交工作区。

## 来源与处理

| 来源 | 差异 | 处理 |
| --- | --- | --- |
| `dev-env-linux_bak` | `config/.gitconfig` | 合入移除公司 Git URL 重写规则的改动 |
| 同上 | `scripts/setup_linux.sh`、`setup_linux_system.sh`、`distro/apt.sh`、`distro/dnf.sh` | 合入发行版探测、包管理接口及驱动 |
| 同上 | `scripts/setup_linux_apps.sh` | 合入版本集中管理/追踪、PathPicker 拼写修复、sheath 绝对路径及 cargo 安装函数生成；冲突按下述规则处理 |
| 同上 | `scripts/setup_macos_apps.sh` | 合入已安装应用 upgrade/uninstall 条件修复 |
| 同上 | `sheath/functions.sh` | 合入 save_env 追加条件、macOS timestamp、独立 FIFO 路径修复 |
| 同上 | `CHANGES.md` | 原样保留备份中的修复说明；最终合并决策以本记录为准 |
| `dev-env-linux.claude.bak` | `CLAUDE.md` | 导入并校正实际 CLI 参数、函数签名、测试说明，标记当前开发目录 |
| 同上 | `.claude/settings.local.json` | 不导入：仅授权旧机器 `/Users/smart` 下备份目录的 find 命令，与项目功能无关 |

Claude 备份中的所有共有项目文件与合并前当前目录内容及权限完全相同。
当前目录已有的 `linux/`、`scripts.bak/`、`sheath.bak/`、本机状态文件、日志、
`test.sh`、`todo` 等全部保留，没有因备份目录缺失文件而删除任何现存文件。

## 冲突决策

以当前目录的安装选择为准：

- 默认自定义工具不恢复 `sdl`。
- 可选系统包继续排除 `nnn`、`kakoune`、`the_silver_searcher`、`fortune-mod`，
  APT 驱动排除对应包 `silversearcher-ag`、`fortune`。
- 可选自定义工具不自动恢复 ImageMagick、dive、grv、trash-cli、FlameGraph，
  保留函数以便通过 `--enable-<app>` 单独启用。
- 保留当前 forgit 下载停用逻辑。
- 保留当前 `config/setup_centos.sh` 的 pcre-devel 排除（只清理一处行尾空格）、
  `common_defines.sh` 的修改、macOS spctl 命令停用。
- CentOS 加密策略说明随 hook 移入 DNF 驱动。
- sheath 路径使用备份的 `${REPO_ROOT}/sheath` 绝对路径方案，替代当前依赖工作目录的方案。

## 合并中修复的问题

以下问题先通过隔离脚本复现，再修复：

1. 新驱动已改为 `DISTRO_PKG_APPS`，安装批次仍引用旧 `dnf_apps`：统一使用新数组。
2. 版本 API 查询失败在 `set -e` 下退出：捕获失败，保留默认版本。
3. 连续多个 `--disable` 参数因 unset 产生稀疏索引而触发 `set -u`：遍历实际数组索引。
4. Go 版本 JSON 解析只接受无空格格式：允许 JSON 字段和冒号之间的空白。

## 验证与范围

- 33 个 Shell 文件 `bash -n` 通过，`git diff --check` 通过。
- APT/DNF × optional true/false 四组模拟安装流程通过，验证 enable/disable 及当前排除项。
- 离线版本回退、Go JSON 空白解析通过。
- 模拟 Homebrew：已安装软件执行 upgrade/uninstall，未安装软件跳过。
- sheath 的 save_env 去重、macOS timestamp、并发 batch 调用通过。
- 原 `sheath/functions_test.sh` 为日志演示，故意调用 fatal/panic，退出码 1；
  已比较合并前快照，退出码与输出一致。
- 对两个备份目录做文件哈希及权限核对：均未改变；当前原有文件全部保留。

没有执行完整 `build.sh`，因为它会实际安装软件、修改系统配置；后续第一批优化已移除删除整个源码目录的退出 trap。
驱动合入不代表全部自定义安装函数已兼容 APT；部分旧函数仍直接调用 rpm/dnf。
网络版本解析用 fixture 验证，未验证远端下载地址或进行真实下载安装。

## 回滚材料

合并前完整文件快照（排除 `.git` 与工作计划）及原始 Git diff：

`/private/tmp/dev-env-linux-before-merge-jyl4d6e4`

差异分析、验证结果位于 `.planning/2026-10-13-merge-backup-directories/`。
此次仅修改工作区，未创建 Git 提交。
