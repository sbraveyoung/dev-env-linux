# Bug 修复与代码优化记录

## sheath/functions.sh

### 1. `save_env()` — 追加条件判断反了

**问题：** `[ ${exist} -ne 0 ]` 表示"行已存在才追加"，逻辑与意图相反，
会导致同一变量被无限重复写入 `.env`，而不存在的行反而不会写入。

**修复：** 改为 `[ "${exist}" -eq 0 ]`，仅当 `.env` 中尚无该行时才追加。

---

### 2. `timestamp()` — 不跨平台

**问题：** `date --rfc-3339=s -d @$1` 是 GNU coreutils 语法，在 macOS（BSD date）上会直接报错。
项目同时支持 macOS 和 Linux，此函数在 macOS 下完全不可用。

**修复：** 用 `is_mac` 判断分支，macOS 使用 `date -r "$1" '+%Y-%m-%d %H:%M:%S %z'`。

---

### 3. `batch()` — FIFO 路径固定，存在并发竞争

**问题：** 写死 `/tmp/fd1` 作为命名管道路径。当同一台机器上多个用户或多个脚本实例并发执行时，
会争抢同一文件，导致死锁或数据混乱。

**修复：** 改用 `mktemp -u` 生成唯一临时路径，创建后立即 `rm -f`（UNIX inode 语义保证 FD 仍有效）。

---

## scripts/setup_macos_apps.sh

### 4. `upgrade_darwin_xxx` / `uninstall_darwin_xxx` — 逻辑全部反了

**问题：** 生成函数中的条件是 `if brew list ${app}`，`brew list` 在应用**已安装**时返回 0（真），
因此函数在已安装的情况下进入分支、打印 warning 并 return，永远不会执行 upgrade 或 uninstall。

**修复：** 改为 `if ! brew list ${app} &>/dev/null`，未安装才警告并跳过。

---

## scripts/setup_linux_apps.sh

### 5. 版本号硬编码，散落函数体内

**问题：** `go1.21.0`、`v0.9.2`、`v2.17.7` 等版本字符串直接写在各函数的 URL 和路径里，
升级时需要找到并修改多处，容易遗漏。

**修复：** 在文件顶部统一声明 6 个版本变量（`GOLANG_VERSION`、`DIVE_VERSION` 等），
函数体内改为 `${VERSION_VAR}` 引用。

---

### 6. `--disable-xxx` 在 Linux 下完全无效

**问题：** disable 逻辑中的循环用了 `brew_apps[i]`（macOS 变量），
而非 `dnf_apps[i]`（Linux 变量），导致 `--disable-xxx` 参数在 Linux 下无任何效果。

**修复：** 将循环内的判断条件改为 `${dnf_apps[i]}`。

---

### 7. `conifig_linux_PathPicker` — 函数名拼写错误

**问题：** 函数名写成了 `conifig_linux_PathPicker`（conifig），
`common_defines.sh` 中按约定调用的是 `config_$1_$3`，因此 PathPicker 的配置步骤（创建 `fpp` 软链接）从未被执行。

**修复：** 改为 `config_linux_PathPicker`。

---

### 8. `install_linux_this-repo` — heredoc 中路径无法展开

**问题：** heredoc 里写的是 `(cd ../sheath && pwd)/constant.sh`，
缺少 `$()` 包裹，该表达式在 heredoc 展开时被当作字面字符串写入 `.bashrc`，
导致 `source` 命令找不到文件，sheath 所有功能失效。

**修复：** 提前用 `_sheath_path="$(cd "${REPO_ROOT}/sheath" && pwd)"` 计算绝对路径，
在 heredoc 中引用 `${_sheath_path}`，确保写入 `.bashrc` 的是实际可用的绝对路径。

---

### 9. 20 个 `cargo install` 函数重复样板

**问题：** `broot`、`exa`、`fd-find` 等 20 个工具的安装函数体完全相同（`~/.cargo/bin/cargo install <name>`），
逐一定义导致代码冗长，新增工具时需手动复制粘贴。

**修复：** 用循环 `eval` 统一生成这些函数；`lsd`（需从 git 安装）单独保留。

---

### 10. 版本号自动追踪（新增功能）

**背景：** 版本常量若长期不更新，安装的工具会越来越旧。

**实现：**
- 新增 `_github_latest_version()` 函数，通过 GitHub Releases API 查询最新版本。
- 新增 `_resolve_latest_versions()` 函数，依次查询各工具最新版并覆盖默认值。
- 脚本启动时自动调用，网络不可达或 API 限流时静默回退到硬编码默认值。
- 可通过环境变量 `SKIP_VERSION_CHECK=true` 跳过，适用于离线/CI 场景。
- 支持 `GITHUB_TOKEN` 环境变量，避免 GitHub API 匿名请求 60 次/小时的速率限制。
