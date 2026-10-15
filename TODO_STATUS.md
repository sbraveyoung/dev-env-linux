# TODO 与空实现处理状态

本轮处理活动代码中的待办及空实现，历史归档、生成锁、测试数据中的 TODO/XXX 不作为开发任务。
尚未全部完成：YuvEye 和 StreamEye 缺少必要来源信息，保留明确失败入口，未把它们标记为安装成功。

| 项目 | 状态与行为 |
| --- | --- |
| bak 多文件、时间戳 | 已实现，支持文件/目录/符号链接，每次生成唯一备份容器 |
| unbak/umbak 比较恢复 | 已实现，相同内容跳过，不同内容先备份，恢复不会把旧目录合并到新目录 |
| 当前日志级别 | 已实现 LOG_LEVEL；默认 trace，支持 quiet，fatal/panic 保持退出行为 |
| scd 在当前/子目录生效 | 已实现 direnv 授权环境继承与卸载；不直接 source .env；授权失败也清理前一个目录的环境 |
| cdls | 已实现 scd 后列目录，eza/exa/ls 按可用性回退 |
| source 时路径定位 | 移除旧试验注释，现有 BASH_SOURCE 定位保留，异地 source 回归通过 |
| git_clone_nx 弃用 TODO | 过时注释已修正；保留被实际调用的 Git 元数据校验与重入能力 |
| Linux 构建依赖下沉 | 已有 managed_dependencies 按后端处理，清理滞后 TODO |
| SSH 配置替代手写登录 | 已实现，relay 默认使用 OpenSSH；配置部署到 ~/.ssh/config，修正原来的无效文件名并支持旧快照迁移；Host mac 指向 host.docker.internal |
| VS Code 配置 | 已实现默认设置与 code CLI 链接，保护用户已有 JSONC 和同名文件 |
| kitty 配置 | 已实现配置模板与显式安装选择，不覆盖已有配置 |
| He3 | 已接入官方 Homebrew tap，支持 install/upgrade/uninstall，--only/--enable 可独立选择 |
| H264Naked / FlvParser / YUView | 已实现固定提交源码构建、依赖部署与应用链接；支持安装/升级/回滚/卸载，失败不发布半成品，拒绝覆盖其他 App |
| YuvEye | 待来源信息：仓库只有软件名，未能确认对应官网或项目；不能据此选择同名或近似名称的软件 |
| StreamEye | 待供应商 macOS 安装包及授权信息；不自动提交官网申请表或代用第三方下载 |
| forgit 停用、grv ARM 资产限制 | 保留已有选择与真实平台限制，不作为空实现消除 |
| 发行版空配置 hook / LazyVim 自定义模板 | 前者是可选接口的显式无操作，后者继承 LazyVim 默认行为；不是缺失安装功能。无用途的 Vim 空 hook 已移除 |

## 用法变化

```bash
bak file1 'directory with spaces' > backup-paths.txt
unbak '/path/to/file.bak.20261015T120000.XXXXXX'
LOG_LEVEL=warning
scd project/subdirectory
# 项目环境需用户在信任后显式执行 direnv allow；普通 cd 不会自动接管。
```

relay 读取 OpenSSH 的 Host/User/IdentityFile/ProxyJump，参数原样传递；mac 的 User 可在 SSH 配置中设置。
需要旧 Expect 登录时显式设置 DEV_ENV_LEGACY_LOGIN=true，原 HOST_USER/COMPANY_USER 等变量仅供该兼容模式使用。

macOS Qt 工具的来源、完整提交、依赖、项目文件、bundle 路径、补丁声明在 config/software.json。
默认链接到 ~/Applications，可通过 DEV_ENV_APPLICATIONS_DIR 修改；已构建版本保留在 APP_PATH/macos。
用户已有普通 App 目录、其他应用链接、VS Code/kitty 配置不会被覆盖。

## 上游来源与验证界限

- [He3 官方 tap](https://github.com/he3-app/homebrew-he3/blob/main/Casks/he3.rb)。
- [H264Naked 官方源码](https://github.com/shi-yan/H264Naked)、[FlvParser 官方源码](https://github.com/imagora/FlvParser)、[YUView 2.14](https://github.com/IENT/YUView/releases/tag/v2.14)。
- H264Naked 的旧 config.guess 不识别 ARM64：从 configure.ac 经 autoreconf 重新生成构建系统。
- FlvParser 的 resource.qrc 路径大小写错误：应用 config/patches 中的生成源补丁，不修改生成的 C++ 或 Makefile。
- YUView 的 Mac bundle 位于 YUViewApp/YUView.app，已核实上游工程并声明该路径。
- [Homebrew qt@5](https://formulae.brew.sh/formula/qt@5) 当前 deprecated，计划 2027-05-19 disable。这些旧应用仍使用 Qt5，迁移 Qt6 需要另行适配上游源码。
- [StreamEye 官方下载说明](https://elecard.com/software) 需要联系/申请；演示许可证明确不支持 VM 或远程协议激活。未申请、购买或激活产品。
- macOS 部分的安装流程/文件保护通过 Linux 外部工具替身回归；三个真实源码在 Ubuntu ARM64 编译、以临时 HOME 离屏启动。没有运行真实 macOS 构建、安装或系统配置，不能据此宣称 macOS GUI、签名、授权或媒体解析已全面验证。

完整日志与源码指纹见 [validation/todo-completion](validation/todo-completion)。
