#!/usr/bin/env bash

set -exuo pipefail

#if [[ ! -f .env ]]
#then
#    #save_env "input your username of docker hub:" user_name
#    #save_env "named the new image:" image_name
#    #save_env "the image version:" image_version
#    save_env "normal username in image you want:" normal_user
#    save_env "normal password in image you want:" normal_passwd
#    save_env "root password in image you want:" root_passwd
#    save_env "named the container:" container_name
#    
#    #If you want to use ssh easily, prepare:
#    #XXX: optional
#    save_env "your host username:" host_user
#    save_env "your host password:" host_passwd
#    save_env "your company username:" company_user
#    save_env "your company password:" company_passwd
#    save_env "your company relay addr:" relay_addr
#fi
#
#. .env

docker build -t $(whoami)/${LINUX_ENV_NAME}:latest --network=host --build-arg NORMAL_USER=${LINUX_USER} --build-arg NORMAL_PASSWD=${LINUX_NORMAL_PASSWD} --build-arg ROOT_PASSWD=${LINUX_ROOT_PASSWD} -f dockerfile_centos ..
