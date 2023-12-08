中文 | [EN](./README_EN.md)

# SheAth 是什么

SheAth 是 Shell 和 Athena 两个单词的缩写，每个单词取前三个字母，即 She-Ath。

Athena 为我希望在各个编程语言领域积累的一些基础库，本为‘雅典娜’之意，象征着希腊女神，也希望这个项目能够成为每一位软件开发人员心目中的希腊女神。

Shell 就是终端命令提示符，因此用两个单词的缩写来命名本项目，意思是尽可能做成一个 shell 的基础库，包括 alias 快捷键、各种常量、函数、环境、配置等。

# 关于 SheAth

## alias 快捷键

快捷键其实每个人都有不同的喜好，有很大的主观性。同一个命令，有人可能喜欢直接敲原命令，有人可能习惯重定义为 A，其他人可能喜欢重定义为 B。所以这里加的比较少，也是我个人的一个偏好。比如清屏命令 `clear` 映射为 `c`，`cat` 映射为 `bat`，`ls` 映射为 `exa` 以及一些 git 相关的映射等。你可以从 [alias.sh](./alias.sh) 中找到。如果你需要，也可以自己往里面添加。

## 方便好用的小函数

shell 基础库，基础在哪里？我觉得就是提供一些小功能来方便大家使用，提升日常工作效率，也确确实实解决了我工作中的很多痛点。所以这些小函数也是本项目一个小特色。目前提供的函数（部分）如下所示，你可以当成命令直接在终端中使用。要了解所有已有的功能，请查看 [functions.sh](./functions.sh) 文件。

* parse_git_branch: 获取当前 git 分支。目前主要用在终端的 PS1 配置里面；
* echo_date: 格式化当前时间，精确到秒。目前也主要用在终端的 PS1 配置里面；
* save_origin_env/restore_origin_env：保存/恢复某个环境变量。很多时候我们在某个项目下做一些测试，需要单独配置一些环境变量。但如果直接 `export` 则会逃逸到全局环境变量，污染原变量空间。因此可以在改项目下放置两个 `.env`/`.unenv` 文件，`cd` 到该目录时会自动加载环境变量，离开时会自动恢复。这两个函数不用手动调用，是自动的；
* smart_cp：智能拷贝，有多智能呢？也就是要拷贝到的目标目录如果不存在会自动创建出来，暂时还没想到其他更智能的场景；
* save_env：前面说 `.env`/`.unenv` 会自动加载，但文件内容还得你自己写。这个函数就是提供一个 helper，快速写入某个环境变量到这两个文件中；
* jcurl：作为开发者，很多时候需要测试某些接口返回的 json 数据，这个函数可以通过 `curl` 发送请求，并把返回 json 数据格式化展示。（现在有些鸡肋了，可以直接用 [`httpie`](https://github.com/httpie/cli)）;
* mkdir_and_cd：创建一个目录再进入该目录，一键完成。该命令也不用手动调，已经 alias 到 `mkdir` 上了。如果要调用原生 `mkdir` 命令可以用 `\mkdir` 或 `command mkdir`；
* every：定时自动执行某条命令，直到用 `Ctrl-c` 退出。在某些异步场景下轮询计算结果还是很有用的；
* timestamp：将 Unix 时间戳转成 human friendly 的可读格式；
* bak：快捷备份文件。`bak file` 等价于 `cp file file.bak`；
* mbak：`bak` 的 `mv` 版本，相当于 `mv file file.bak`；
* unbak/umbak：恢复文件，分别对应 `cp` 版本和 `mv` 版本；
* touchx：快速创建带可执行权限的文件，不用先 `touch`，再 `chmod`；
* printf2stdout/printf2stderr；分别向标准输出和标准错误输出打印日志，支持 printf 能力，支持 trace/debug/verbose/info/warning/error/fatal/panic/quiet 9 个日志级别，每个级别有不同的前景及背景颜色区分。注意：**如果是 panic/fatal 级别，输出后会退出当前进程**；
* is_mac/is_linux：判断当前系统环境；
* command_exist：判断某条命令是否存在，支持 shell 内建命令、`${PATH}`路径中的可执行文件、函数命令、alias 命令等;
* batch：并发执行批处理任务，并发度可自定义；
* do_if：当条件为真时执行某条命令；

## shell 环境配置

## 编程语言相关

### golang
* GOPATH: 
* GOROOT:

### python

### c++

## 终端相关
