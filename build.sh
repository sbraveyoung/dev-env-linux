#!/usr/bin/env bash

set -exuo pipefail

export OPTIONAL=false
export WITH_LINUX=false             # docker or vm
export LINUX_ENV_NAME=linux-dev-env # linux_dev_env is invalid
export LINUX_USER=$(whoami)
export LINUX_NORMAL_PASSWD=""
export LINUX_ROOT_PASSWD=""
export OPERATOR=install # or upgrade/uninstall
export ENABLE_APPS=()
export DISABLE_APPS=()
export CONCURRENT=5
export TIMEOUT=7200 # 2hours
declare -A APP_FLAGS
export APP_FLAGS
export SYSTEM=$(uname -s | tr 'A-Z' 'a-z')
export REPO_ROOT=$(pwd)
export CACHE_FILE=${REPO_ROOT}/.$(basename ${REPO_ROOT})

[ $# -gt 0 ] && {
	for arg in "$@"; do
		case ${arg} in
		--help*)
			#TODO:
			;;
		--only=)
			#TODO: install/upgrade/uninstall something only
			;;
		--optional=*)
			case ${arg#--optional=} in
			true | True | t | T | 1)
				OPTIONAL=true
				;;
			false | False | f | F | 0)
				OPTIONAL=false
				;;
			*) ;;
			esac
			;;
		--with-linux=*)
			# vm or docker
      case ${arg#--with-linux=} in
        vm | docker)
          WITH_LINUX=${arg#--with-linux=}
          ;;
        *)
          printf2stderr "error" "invalid valud of argument --with-linux: %s\n" "${arg$--with-linux=}"
          exit 1
          ;;
      esac
			;;
		--linux_env_name=*)
			LINUX_ENV_NAME=${arg#--linux_env_name=}
			;;
		--linux_user=*)
			LINUX_USER=${arg#--linux_user=}
			;;
		--linux_normal_passwd=*)
			LINUX_NORMAL_PASSWD=${arg#--linux_normal_passwd=}
			;;
		--linux_root_passwd=*)
			LINUX_ROOT_PASSWD=${arg#--linux_root_passwd=}
			;;
		--operator=*)
			OPERATOR=${arg#--operator=}
			;;
		--enable-*)
			ENABLE_APPS=("${ENABLE_APPS[@]}" "${arg#--enable-}")
			;;
		--disable-*)
			DISABLE_APPS=("${DISABLE_APPS[@]}" "${arg#--disable-}")
			;;
		--concurrent=*)
			CONCURRENT=${arg#--concurrent=}
			;;
		--timeout=*)
			TIMEOUT=${arg#--timeout=}
			;;
		--app_flag=*)
			# eg: --app_flag=wetype=xxx
			app_flag=${arg#--app_flag=}
			if [[ ${app_flag} == "" ]] || [[ ! ${app_flag} =~ "=" ]]; then
				printf2stderr "error" "invalid argument: %s\n" "${arg}"
				exit 1
			fi

			items=${app_flag//=/ }
			app="${items[0]}"
			unset "items[0]"
			APP_FLAGS[${app}]=${APP_FLAGS[${app}]}"/"${items}
			;;
		--clean_cache)
			rm -rf ${CACHE_FILE}
			exit 0
			;;
		*)
			printf2stderr "error" "arg:%s is not supported.\n" "${arg}"
			exit 1
			;;
		esac
		shift
	done
}

cd scripts
source common_defines.sh

if is_mac; then
	source setup_macos.sh # exec setup_macos.sh in current process in order to use array variables which have be defined.
elif is_linux; then
	source setup_linux.sh
else
	printf2stderr "error" "unsupported system:%s.\n" "$(uname -s)"
	exit 1
fi
