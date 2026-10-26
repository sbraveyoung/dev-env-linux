# 软件清单维护

[config/software.json](config/software.json) 是人工维护的唯一软件声明源，目前有 143 个软件条目。
条目包含跨平台声明、手动/停用工具，不代表全部软件已在每个平台通过安装认证。
Shell/Python 安装器读取声明；构建不会重新生成或覆盖这份文件。
原 scripts/software.json 已迁移并移除。

## 改哪里

| 内容 | JSON 路径 |
| --- | --- |
| Linux 默认安装顺序 | profiles.linux-default |
| 可手动选择的 Linux 工具 | profiles.linux-manual（文档分组，不会自动安装） |
| macOS 基础/可选/开发分组 | profiles.darwin-base / darwin-optional / darwin-development |
| APT/DNF 基础和可选系统依赖 | drivers.apt / drivers.dnf |
| 软件来源及 Go/Cargo/pip/npm/Git/源码后端 | apps.<ID>.managed |
| 共享后端的显式期望版本 | apps.<ID>.managed.version（可选） |
| 原生包映射 | apps.<ID>.native，发行版 ID 优先于 apt/dnf |
| macOS 安装来源、可选官方 tap | apps.<ID>.darwin / darwin.tap |
| macOS 已有 App 检测 | darwin.app_bundles / bundle_ids / app_directories |
| macOS Qt 源码构建 | darwin.installer=qt；source_url / revision / project / bundle / brew_dependencies |
| Go/Rust 默认安装版本 | apps.golang.version.default / apps.rust.version.default |
| 自定义下载 URL、架构与校验来源 | 对应 app 的 download_url / targets / checksum_url |
| 后端构建依赖 | backend_dependencies |

APT/DNF/Homebrew 软件版本由对应渠道管理，版本清单记录实际安装状态；Homebrew 可使用如 ffmpeg@6 的版本化 formula。
特殊安装步骤、命令别名和用户配置仍在对应 hook 中；新增共享后端软件无需编写单独的安装函数。
新增 SDK 或具有新安装行为的自定义工具仍需要实现 hook。

## 示例

以下是 apps 中一个条目的示例，可在 managed 下添加期望版本：

```json
"ccat": {
  "managed": {
    "backend": "go",
    "package": "github.com/jingweno/ccat",
    "version": "v1.1.0"
  }
}
```

不设置 managed.version 时，install 依次采用本机锁、仓库锁、注册表解析；upgrade 解析新的版本。
设置时 install/upgrade 均遵守声明的版本，原有版本仍保留供显式 rollback。
Git/源码可以通过 managed.ref 选择上游 tag，解析结果记录为确切提交；修改 ref 后执行 upgrade。
若同一版本目录的已安装来源与新声明不同，安装器会拒绝复用，并保留原文件。
此时选择不同的新版本或独立的 APP_PATH/BIN_PATH，避免把旧来源当成新来源。

Go/Rust 使用声明中的默认安装版本，已有 GOLANG_VERSION/RUST_VERSION 环境变量优先。
SKIP_VERSION_CHECK=false 仍显式启用 Go/grv 的网络版本追踪；Rust upgrade 保持原有 stable 升级行为。
WeType 的 WETYPE_VERSION、URL、zip/app 名称也在 darwin 声明下，尚未进行真实 macOS 安装验证。

添加 Go/Cargo/pip/npm/Git/源码工具时，在 apps.<ID>.managed 填写后端和来源，
即可用 --enable-<ID> 或 --only=<ID> 选择。需要默认安装时再加入 profiles.linux-default。
Mac brew 工具填写 darwin.backend=brew 和 package，并加入相应 Darwin 分组。
现有 --only、--enable、--disable、--optional 和环境变量覆盖方式保留。

## 查询与校验

这些命令在已有隔离 Linux VM 中运行，不在 Mac 宿主执行项目测试：

```bash
python3 scripts/catalog.py validate
python3 scripts/catalog.py list --platform linux --distro apt --distro-id ubuntu
python3 scripts/catalog.py list --platform linux --distro dnf --distro-id fedora
python3 scripts/catalog.py list --platform darwin
python3 scripts/catalog.py profile linux-default
bash scripts/check.sh
```

list 只读配置和仓库锁，不安装软件或查询网络；输出来源、后端、默认选择和版本信息。
validate 检查重复 JSON 键、嵌套类型、未知字段、必需分组、分组引用、安全名称、后端、版本与模板占位符。
Darwin 分组中的软件必须具有 darwin 声明；commands 必须是相对路径，禁止绝对路径和 ..；
下载和引导来源必须使用 HTTPS。错误包含字段路径，例如 apps.ccat.managed.commands。
新增字段时同时更新 scripts/catalog.py 的校验规则，避免把 verison 等拼写错误当作有效配置。
check.sh 和 CI 先验证声明；macOS 入口在系统设置操作前验证声明。
模板支持 {version}、{arch}、{target}；{release} 取版本中下划线前的部分，用于 WeType。
Shell 消费者只评估经过引用的数组/赋值，不把配置字段当作任意命令执行。

临时验证另一份配置时，在 VM 指定 DEV_ENV_SOFTWARE_CATALOG=/absolute/path/software.json；
所有安装消费者使用同一个变量，默认不需要设置。只读 CLI 也支持 --config FILE。
managed.py、managed_gc.py、export_lock.py、Go 下载校验和 tests/full_install.py 共享同一个校验读取入口；
无效声明会在安装、清理、收据读取或批量验证结果目录创建之前失败。
full_install.py 只验证当前 linux-default 中的软件；仅当 Go/Rust 在该分组中时才将它们提前。
Darwin 清单中，未实现的 hook 显示 not implemented；不再被标记成 Homebrew 管理版本。
默认清单的迁移基线保存在 validation/software-catalog，不参与运行或测试的期望值；
后续正常调整分组无需同步修改一份重复测试清单。

## 声明与安装锁

software.lock.json 是由真实安装记录生成的精确版本、依赖和提交快照，不能手改。
调整声明并在 VM 验证后，继续用 scripts/export_lock.py 生成锁；跨发行版收据用 --merge 合并。
本轮没有为了移动配置重写这份生成物，原有已验证版本保留。

本轮验证结果位于 [validation/software-catalog](validation/software-catalog)：三个隔离发行版默认 76 应用复验通过，
并在独立前缀真实验证了声明固定 ccat v1.0.0 → 配置改为 v1.1.0 后升级 → 回滚 v1.0.0，命令运行通过。
macOS 只通过 Linux 模拟回归；宿主未运行安装或测试脚本。

后续统一校验验证见 [validation/software-catalog-followup](validation/software-catalog-followup)：
三个隔离发行版各 79 项回归及静态检查通过，另有无网络、无宿主挂载容器验证。
此轮没有从零重装默认 76 项软件，也未修改生成的仓库锁。

## 补齐的 macOS 安装入口

He3 使用官方 he3-app/he3 tap；kitty 和 direnv 可通过 --only/--enable 显式选择，不加入默认安装分组。
VS Code 与 kitty 的默认配置模板位于 config/vscode/settings.json 和 config/kitty/kitty.conf；已有用户配置（包括 JSONC）保持原样。
VS Code 的 code CLI 优先使用安装的 App 内脚本，已有同名用户文件不覆盖。

H264Naked、FlvParser、YUView 使用 darwin.installer=qt，revision 为完整 40 位提交；
源码下载、项目文件、依赖、bundle 路径、构建补丁均在声明中维护。升级提交后执行 upgrade。
Qt 工具默认发布到 ~/Applications，DEV_ENV_APPLICATIONS_DIR 可覆盖位置；构建位于 APP_PATH/macos，
只替换安装器管理的应用链接，拒绝覆盖其他 App。支持 install / upgrade / rollback / uninstall；
卸载仅移除所属链接，保留已构建版本以供回滚。
Qt5 是这些旧应用的兼容依赖，已由 Homebrew 标记 deprecated，计划 2027-05-19 disable；不把 Linux 编译验证当成 macOS 认证。

YuvEye 身份/来源和 StreamEye 的供应商安装包仍需补充，具体状态见 TODO_STATUS.md。

## macOS 已有软件的声明

`darwin.app_bundles` 是完整 `.app` 文件名列表；`bundle_ids` 可选，声明后按 Info.plist 中的
CFBundleIdentifier 精确匹配，即使用户改过 App 名称也能识别。同名但 ID 不同的 App 不匹配。
未声明 ID 时按文件名匹配完整应用包，不把空目录或缺少可执行文件的残留当成已安装。
这里是安装状态检测，不是代码签名或发布者身份认证。

默认只读扫描 `/Applications`、`~/Applications` 及下一层应用目录；
`DEV_ENV_APPLICATIONS_DIR` 替换系统 App 扫描位置，也控制 Qt 发布位置。
额外扫描位置写入 `darwin.app_directories`，支持绝对路径与 `~/`，例如 WeType 的 Input Methods 目录。
Qt 源码应用默认从 `darwin.bundle` 提取 App 名称，无需重复声明。
Homebrew hook 也查询 `brew list`；不根据任意同名 PATH 命令推断手动 CLI 软件的版本或归属。

App 名称主要核对自 [Homebrew 官方 cask API](https://formulae.brew.sh/docs/api/)，
每项 `/api/cask/<package>.json` 的 app artifact；ID 可从已确认的主程序 plist 或 cask 的主程序退出声明核对。
不要把 helper/agent 的 ID 当作主程序 ID。清单是维护源，安装时不在线下载检测规则。
不同历史版本变更过名称或 ID 时，应在对应列表中添加核实后的别名，不能用宽泛通配符匹配其他应用。
具体保护和限制见 [INSTALLATION_SAFETY.md](INSTALLATION_SAFETY.md)。
