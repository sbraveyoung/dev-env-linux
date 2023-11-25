#!/usr/bin/env bash

set -exuo pipefail

source ../sheath/functions.sh

# $1-: command to be executed and all of args
execute_if_not_success() {
	if ! command_exist git || ! command_exist grep; then
		if is_mac; then
			sudo brew install git grep
		elif is_linux; then
			sudo dnf install -y git grep
		fi
	fi

	record_file=${CACHE_FILE}
	if [[ ! -f ${record_file} ]]; then
		touch ${record_file}
	fi

	local key=""
	for item in "$@"; do
		# XXX: has any better way?
		key="${key}_${item}"
		key=${key#\_}
	done

	set +e
	success=$(grep ${key} ${record_file} | wc -l)
	set -e
	if [[ ${success} -ne 0 ]]; then
		printf2stdout "info" "command was executed success, skip:%s\n" ${key}
		return
	fi

	$@ #if fail, this function will exit from here

	# TODO: write command with expire time
	echo ${key} >>${record_file}
}

# $0: cmd: install
# $1: macos or linux
# $2: tmp_dir
# $3: app
install() {
	if command_exist "preinstall_$1_$3"; then
		(execute_if_not_success preinstall_"$1"_"$3" "$2")
	fi

	if ! command_exist "install_$1_$3"; then
		printf2stderr "error" "%s install function of %s is not defined.\n" "$1" "$3"
		return 1
	fi
	(execute_if_not_success install_"$1"_"$3" "$2")

	# configuration is unnecessary, try to invoke it.
	if command_exist "config_$1_$3"; then
		(execute_if_not_success config_"$1_$3" "$2")
	fi
}

# $0: cmd: upgrade
# $1: macos or linux
# $2: tmp_dir
# $3: app
upgrade() {
	if command_exist "preupgrade_$1_$3"; then
		(execute_if_not_success preupgrade_"$1"_"$3" "$2")
	fi

	if ! command_exist "upgrade_$1_$3"; then
		printf2stderr "error" "%s upgrade function of %s is not defined.\n" "$1" "$3"
		return 1
	fi
	(execute_if_not_success upgrade_"$1"_"$3" "$2")
}

# $0: cmd: uninstall
# $1: macos or linux
# $2: tmp_dir
# $3: app
uninstall() {
	if command_exist "preuninstall_$1_$3"; then
		(execute_if_not_success preuninstall_"$1"_"$3" "$2")
	fi

	if ! command_exist "uninstall_$1_$3"; then
		printf2stderr "error" "%s uninstall function of %s is not defined.\n" "$1" "$3"
		return 1
	fi
	(execute_if_not_success uninstall_"$1"_"$3" "$2")
}

# $1: concurrent
# $2-: need to be installed/upgraded/uninstalled apps
batch_wrapper() {
	batch "${CONCURRENT}" "${OPERATOR} ${SYSTEM} ${tmp_dir}" "$@"
}

# TODO: deprecated, using do_if instead
# $1-(n-1): git url to be clone and git args
# $n(the last arg): local path
git_clone_nx() {
	args_num=$#
	local_path=${!args_num}

	if [[ ! -d ${local_path} ]]; then
		git clone "$@"
	fi
}

# TODO: deprecated, using do_if instead
# $1-(n-1): url to be downloaded and wget args
# $n(the last arg): local path
wget_nx() {
	args_num=$#
	local_path=${!args_num}

	if [[ ! -e ${local_path} ]]; then
		command wget "$@"
	fi
}
