#!/usr/bin/env bash

#set -euo pipefail
set -uo pipefail

#smart cd: can import environment variable you need automatically
#maybe https://github.com/hyperupcall/autoenv or https://direnv.net/ is better
#scd() {
#	#TODO: take effect in current dir and sub dir.
#	[ -f .unenv ] && . .unenv
#	cd $1
#	[ -f .env ] && . .env
#}
#
#
#cdls() {
#	scd $1
#	exa --all
#}

# get the path of current script, instead of shell path
#get_self_dir() {
#	echo $(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
#	# XXX: have bug when this script file was imported by `source`
#	# echo $(dirname $(readlink -f "$0"))
#	# echo $(cd "$(dirname "$0")" && pwd)
#}
#source $(get_self_dir $0)/constant.sh
#source $(dirname $(readlink -f "$1"))/constant.sh
source $(dirname ${BASH_SOURCE[0]})/constant.sh

parse_git_branch() {
	git branch 2>/dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/ [\1]/'
}

echo_date() {
	date +'%Y/%m/%d %H:%M:%S'
}

echo_sentence() {
	quo=$(fortune -s)
	echo $quo
	#echo `trans $quo` # toooooo slow!
}

save_origin_env() {
	eval ORIGIN_$1=\${$1}
}

restore_origin_env() {
	ORIGIN_KEY=$(echo ORIGIN_$1)
	eval $(echo $1)=${!ORIGIN_KEY}
	unset ORIGIN_$1
}

smart_cp() {
	local args=$#
	if [[ ${args} -lt 2 ]]; then
		return 1
	fi

	local dst_dir=$(dirname ${!args})
	if [[ ! -d ${dst_dir} ]]; then
		mkdir ${dst_dir}
	fi
	cp $@
}

# usage: save_env "please input value:" test_var
function save_env() {
	read -p "$1" -r $2
	eval line="$2=\${$2}"
	[[ -f .env ]] || {
		echo "${line}" >>.env
		return 0
	}
	exist=$(grep ${line} .env | wc -l)
	[ ${exist} -ne 0 ] && {
		echo "${line}" >>.env
	}

  # TODO: write to .unenv also?
}

# deprecated, for autojump
jls() {
	j $1
	exa --all
}

jcurl() {
	curl $1 | jq
}

mkdir_and_cd() {
	dir_count=$#

	# use command to avoid infinite recursion
	command mkdir $@
	[ $? -eq 0 ] && cd ${!dir_count} #cd the last dir
}

#maybe watch command is better!
every() {
	t=$1
	shift

	while true; do
		$@
		sleep $t
	done
}

echo_last_status() {
	[ $1 -ne 0 ] && echo x || echo y
}

timestamp() {
	date --rfc-3339=s -d @$1
}

bak() {
	#TODO: support multifile
	#TODO: backup with timestamp suffix
	local origin=$1
	local new=$1.bak
	if [[ -e ${origin} ]]; then
		if [[ -d ${origin} ]]; then
			smart_cp -r ${origin} ${new}
		else
			smart_cp ${origin} ${new}
		fi
	fi
}

mbak() {
	if [[ -e $1 ]]; then
		mv $1 $1.bak
	fi
}

unbak() {
	#TODO: compare and replace origin file or not?
	cp $1 ${1%.bak}
}

umbak() {
	#TODO: compare and replace origin file or not?
	mv $1 ${1%.bak}
}

touchx() {
	touch $1
	chmod +x $1
}

# TODO: set current log level
# $1: file description
# $2: loglevel
# $3: format string
# $4-: args
# level: quiet/panic/fatal/error/warning/info/verbose/debug/trace
printf_with_level() {
	fd="$1"
	loglevel="$2"
	format_str="$3"
	shift 3

	local control_code=''

	# pays tribute to FFmpeg's loglevel
	case "${loglevel}" in
	quiet)
		return 0
		;;
	panic)
		# text highlight, underline, text color is red, bg color is yellow
		control_code=${CONTROL_CODE_HIGHLIGHT}${CONTROL_CODE_SPERATOR}${TEXT_COLOR_RED}${CONTROL_CODE_SPERATOR}${BACKGROUND_COLOR_YELLOW}
		;;
	fatal)
		# text highlight, text color is red, add underline
		control_code=${CONTROL_CODE_HIGHLIGHT}${CONTROL_CODE_SPERATOR}${CONTROL_CODE_UNDERLINE}${CONTROL_CODE_SPERATOR}${TEXT_COLOR_RED}
		;;
	error)
		# text highlight, text color is red
		control_code=${CONTROL_CODE_HIGHLIGHT}${CONTROL_CODE_SPERATOR}${TEXT_COLOR_RED}
		;;
	warning)
		# text highlight, text color is yellow
		control_code=${CONTROL_CODE_HIGHLIGHT}${CONTROL_CODE_SPERATOR}${TEXT_COLOR_YELLOW}
		;;
	info)
		control_code=${TEXT_COLOR_GREEN}
		;;
	verbose)
		control_code=${TEXT_COLOR_WHITE}
		;;
	debug)
		control_code=${TEXT_COLOR_BLUE}
		;;
	trace)
		control_code=${TEXT_COLOR_PINK}
		;;
	*)
		printf2stderr "error" "invalid loglevel:%s\n" "${loglevel}"
		# printf_with_level /dev/stderr "error" "invalid loglevel:%s\n" "${loglevel}"
		return 0
		;;
	esac

	printf "${CONTROL_CODE_PREFIX}${control_code}${CONTROL_CODE_SUFFIX}${format_str}${CONTROL_CODE_PREFIX}${CONTROL_CODE_CLOSE}${CONTROL_CODE_SUFFIX}" "$@" >&"${fd}"

	if [[ ${loglevel} == "panic" ]] || [[ ${loglevel} == "fatal" ]]; then
		exit 1
	fi
}

# $1: loglevel
# $2: format string
# $2-: args
printf2stderr() {
	#printf_with_level /dev/stderr "$@"
	printf_with_level 2 "$@"
}

# $1: loglevel
# $2: format string
# $3-: args
printf2stdout() {
	#printf_with_level /dev/stdout "$@"
	printf_with_level 1 "$@"
}

is_mac() {
	test "$(uname -s)" == "Darwin"
}

is_linux() {
	test "$(uname -s)" == "Linux"
}

command_exist() {
	command -v "$1"
}

# $1: concurrent
# $2: command
# $3-: data array
batch() {
	[ -e /tmp/fd1 ] || mkfifo /tmp/fd1
	exec 3<>/tmp/fd1
	rm -rf /tmp/fd1
	for ((i = 0; i < $1; i++)); do
		echo >&3
	done

	cmd=$2
	shift 2
	for arg in "$@"; do
		read -u3
		{
			# TODO: timeout
			${cmd} "${arg}"
			echo >&3
		} &
	done
	wait

	exec 3<&-
	exec 3>&-
}

# $1: if condition
# $2-: command if condition is true
do_if() {
	if $(eval test "$1"); then
		shift
		$@
	fi
}
