# 本地历史归档

`legacy/` 保存原根目录的 `linux/`、`scripts.bak/`、`sheath.bak/`，没有修改内容。
目录中的 manifest.json 记录原路径、SHA256 和权限。归档已排除出 Git、Docker 构建上下文和检查。
旧配置可能包含个人信息，请先审查再选择性恢复到当前源码；不要直接发布整个归档。

本地 test.sh、output、安装缓存及日志保持私有并由 .gitignore 排除。
