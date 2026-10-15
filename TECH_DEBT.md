# Brooks-Lint Review

**Mode:** Tech Debt Assessment
**Scope:** 当前仓库的完整执行链、发行版驱动、Sheath 库、Docker/VM 脚本、配置模板及现有验证入口；46 个原已跟踪文件及合并引入的源文件。历史内部备份仅核对重复关系，不作为实现修改目标。未发现 `.brooks-lint.yaml`，使用默认风险项。
**Health Score:** 35/100（本次修复前、按 2 Critical + 7 Warning 的静态诊断扣分；不是兼容性认证）

最优先偿还的是可导致误删源码、卡死或误报成功的执行层债务。第一批已修复并建立回归验证；真实多平台安装、生命周期升级和容器运行仍待后续批次验证。

## Findings

### Critical

**R2 Change Propagation — 全局清理与并发失败传播（已修复）**

Symptom: 两平台 app 脚本均在 EXIT 中 `sudo rm -rf ${tmp_dir}`，tmp_dir 指向共享 CLONE_PATH；旧 batch 的失败 worker 无令牌回收，后续任务卡死，裸 wait 不能汇总失败状态。

Source: The Pragmatic Programmer — Orthogonality；Code Complete — Error-Handling Discipline。

Consequence: 一次安装退出会删除已有源码并破坏指向源码的软链；单个失败影响整个队列，外层可能错误认为安装成功。

Remedy: 保留共享源码，batch 隔离到子进程并逐个收集 PID 的退出码，限制同时运行的任务数；用失败队列和源码保留测试验收。Pain 3 × Spread 3 = 9，accidental。

**R6 Domain Model Distortion — 成功缓存不能准确表示已完成操作（已修复局部问题）**

Symptom: grep 对键进行正则与子串匹配；未引用的 `$@` 拆开参数；不同参数边界可拼成相同缓存键；helper 改变调用方 errexit 状态。

Source: Code Complete — Defensive Programming；Domain-Driven Design — Invariant Ownership（这里只借用状态不变量，不建议引入面向对象模型）。

Consequence: 未执行的命令被误判已完成，失败或不同参数的操作被不正确地跳过。

Remedy: 精确整行匹配与参数边界编码，引用 argv，仅成功写入记录；兼容普通旧 hook 缓存，不改变 helper 调用时的 errexit 设置。版本与升级缓存仍见下方待办。Pain 3 × Spread 3 = 9，accidental。

### Warning

**R1 Cognitive Overload — CLI 混合初始化、字符串拆分和安装副作用（已修复入口）**

Symptom: APP_FLAGS 使用字符串替换后按数组访问；--help 无实现，错误参数要等加载平台脚本才暴露，CONCURRENT=0 可触发卡死。

Source: Code Complete — High-Quality Routines；A Philosophy of Software Design — Information Hiding。

Consequence: 修改参数解析会影响真实系统安装，包含 `=` 或空格的 app flags 被损坏；帮助命令不可安全使用。

Remedy: CLI 解析为单独无安装副作用的模块，保留值原文，入口先处理帮助/校验后再进行平台分发；明确 Bash 4+ 安装要求。Pain 2 × Spread 2 = 4，accidental。

**R5 Dependency Disorder — 源码加载隐式依赖 caller cwd（已修复公共加载与入口）**

Symptom: build.sh 用 pwd 决定 REPO_ROOT，common_defines.sh 临时 cd 到 ../sheath，library 的 source 路径未引用。

Source: The Pragmatic Programmer — Orthogonality；Clean Architecture — Dependency Direction。

Consequence: 绝对路径调用脚本或移动 caller cwd 就会破坏加载；源码路径含空格时报错。

Remedy: 从 BASH_SOURCE 定位公共库与入口，加载不修改 caller cwd；入口从任何位置切换到确定的 scripts 目录。其余叶子安装函数中的未引用路径列入后续平台验收。Pain 2 × Spread 3 = 6，accidental。

**R2 Change Propagation — 执行链缺少回归保护（已建立首批保护）**

Symptom: 唯一 functions_test.sh 是故意输出 fatal/panic 的日志演示，test.sh 是本机环境配置；缺少失败状态、并发和缓存的断言。

Source: Working Effectively with Legacy Code — Characterization Tests / Seams；How Google Tests Software — Change Coverage。

Consequence: 语法检查无法发现队列卡死、误缓存和误删，跨脚本修改只能靠真实安装碰运气。

Remedy: 使用 Python 标准库驱动真实 Shell 机制，临时目录和模拟外部包管理器，建立 21 项回归与统一 check.sh；真实安装/平台矩阵仍待补齐。Pain 2 × Spread 3 = 6，accidental。

**R3 Knowledge Duplication — Docker 与原生安装知识漂移（待推进）**

Symptom: Ubuntu Dockerfile 保留大量与 setup_linux_apps.sh 重复的旧 URL、安装命令和 dotfile 逻辑，CentOS Dockerfile 调用 build.sh 却没有 COPY。

Source: Refactoring — Duplicate Code；The Pragmatic Programmer — DRY。

Consequence: 更新原生版本或配置不能同步修复镜像，容器构建使用另一套过期路径与包名。

Remedy: 先修复构建上下文和用户创建，再复用同一安装入口，按最小 app 集合做镜像 smoke test；不要未经验证升级发行版。Pain 2 × Spread 2 = 4，accidental。

**R5 Dependency Disorder — 发行版驱动抽象尚未闭合（待推进）**

Symptom: apps 脚本里的 dive 仍下载 RPM，ffmpeg/iredis 钩子仍直接调用 DNF；APT 的 Ubuntu PPA 与 DNF 的 RHEL 仓库分别被用于更宽的发行版范围；下载架构写死 amd64。

Source: Clean Architecture — Dependency Inversion；Software Engineering at Google — Dependency Management。

Consequence: 仅探测到 apt-get/dnf 不代表能完整安装；Debian/Fedora/ARM 可能失败在自定义应用或源配置阶段。

Remedy: 实现驱动专属 artifact/前置依赖接口及架构映射，用具体发行版和架构的安装矩阵验证，不宣传未经验证的平台支持。Pain 2 × Spread 2 = 4，accidental。

**R4 Accidental Complexity — 配置与环境入口超过实际实现能力（待推进）**

Symptom: TIMEOUT 被接受但 worker 未执行超时；setup_linux_docker.sh 只有注释；VM 转发丢失 enable/disable/app flags，密码命令不完整。

Source: A Philosophy of Software Design — Tactical Programming；Code Complete — YAGNI。

Consequence: 用户期望的终止与环境配置不会发生，失败安装可能无限等待，参数在跨环境执行时被静默丢弃。

Remedy: 本次帮助明确 TIMEOUT 尚未实施；后续实现可取消的执行超时与进程组清理，完整转发参数，未实现入口显式报错。Pain 2 × Spread 2 = 4，accidental。

**R6 Domain Model Distortion — 生命周期与版本状态表达不完整（待推进）**

Symptom: --operator=upgrade 对多数 Linux 自定义应用没有函数；成功记录没有版本与失效规则，升级命令成功后以后持续命中缓存；版本请求只有连接超时。

Source: Software Engineering at Google — Code Sustainability；Code Complete — Error-Handling Discipline。

Consequence: CLI 的 install/upgrade/uninstall 三种操作在不同 app 上能力不一致；版本变更不会自动反映到缓存，网络连接后卡住不会有总超时。

Remedy: 定义应用操作能力及包管理器默认行为，记录版本/平台/操作/时间并可按应用清理缓存；网络查询加总超时、版本格式与下载完整性验证。Pain 2 × Spread 2 = 4，accidental。

## Debt Summary

| Risk | Findings | Avg Priority | Classification | Intent |
| --- | --- | --- | --- | --- |
| Cognitive Overload | 1 | 4.0 | Scheduled | accidental |
| Change Propagation | 2 | 7.5 | Critical | accidental |
| Knowledge Duplication | 1 | 4.0 | Scheduled | accidental |
| Accidental Complexity | 1 | 4.0 | Scheduled | accidental |
| Dependency Disorder | 2 | 5.0 | Scheduled | accidental |
| Domain Model Distortion | 2 | 6.5 | Scheduled | accidental |

优先级为本次静态分析的维护成本估计，未声称测量了团队工时。当前软件排除项是已有明确选择，保留为 intentional decision，不计作技术债；Shell 编排的大量组合关系不自动算作循环依赖或架构违规。

## Summary

第一批处理共享执行机制和入口，并以可重复的失败路径测试约束行为。后续按 OPTIMIZATION_PLAN.md 推进驱动闭合、版本/超时/生命周期，再处理容器与重复配置；没有执行宿主系统安装，也没有把模拟测试称作真实兼容性验收。

## 续作状态（2026-10-13）

上述报告是修复前诊断。后续已落实超时、原子下载、ARM Go、选择性执行、APT 包兼容、
原生包生命周期、卸载缓存失效、用户目录权限修复，并在隔离 Ubuntu ARM64 VM 内完成真实验证。
Dockerfile 与 VM/Docker argv 转发已重建；源码不挂载到 VM。尚未覆盖每个软件、DNF/macOS 实装，
下载校验和/统一版本缓存/CI 等不宣称已完成。具体结果见 ORB_VALIDATION.md。

## 2026-10-14 更新

全量实装、共享后端生命周期、可信校验/版本锁、DNF 验证、CI 与内部目录归档已完成，
见 [FULL_VALIDATION.md](FULL_VALIDATION.md)。剩余明确范围：原生包旧版本的长期可获得性、
全部 TUI 的交互验收、Fedora/CentOS 的完整应用组合、受管理旧版本的显式垃圾回收，以及 grv 的 ARM 替代方案。

## 2026-10-15 更新

上述维护项已按限定范围实施并实测：三发行版各 76 默认应用，16/15/15 TUI 烟测，
有保护的显式 GC，三个原生根包及闭包的离线精确恢复，独立 lazygit ARM 工具。
ranger 旧脚本入口、共享安装被旧缓存跳过、broot OOM、axel EL 源缺包和构建依赖已修复。
当前具体限制为 GUI/真实 macOS、全部工具的完整业务交互、原生全库存长期归档与服务数据备份；
不是重新将已完成项列为待办。证据见 [MAINTENANCE_VALIDATION.md](MAINTENANCE_VALIDATION.md)。
