# dev-env-linux
A modern linux development environment based on docker, inspired by [the-art-of-command-line](https://github.com/jlevy/the-art-of-command-line), [awesome-shell](https://github.com/alebcay/awesome-shell) and [modern-unix](https://github.com/ibraheemdev/modern-unix), but more than that.

## feature
* Awesome vim from [xvim](https://github.com/adwpc/xvim).
* Awesome tmux with true color support.
* Awesome ssh to connect other mechine including your local host and remote host, support relay mode.
* Useful bash alias and function definition in `~/.bashrc`.
* All tools introduce in [modern-unix](https://github.com/ibraheemdev/modern-unix).
* more waiting for you to discover.

## build

#### environments
You should prepare those environments first:
```shell
export USER_NAME      = your_dockerhub_user
export IMAGE_NAME     = image_name_you_want
export IMAGE_VERSION  = image_version_you_want
export NORMAL_USER    = normal_user_name_you_want
export NORMAL_PASSED  = normal_user_password_you_want
export ROOT_PASSWD    = root_password_you_want
export CONTAINER_NAME = dev-linux-env #or any name you want

#If you want to use ssh easily, prepare:
export HOST_USER        = your_host_user
export HOST_PASSWD      = your_host_passwd
export COMPANY_USER     = your_name_in_company
export COMPANY_PASSWD   = your_passwd_in_company
export RELAY_ADDR       = relay_addr_in_company
```

#### centos
```shell
docker build -t ${USER_NAME}/${IMAGE_NAME}:${IMAGE_VERSION} --build-arg NORMAL_USER=${NORMAL_USER} --build-arg NORMAL_PASSWD=${NORMAL_PASSWD} --build-arg ROOT_PASSWD=${ROOT_PASSWD} -f dockerfile_centos .
```

#### ubuntu
```shell
docker build -t ${USER_NAME}/${IMAGE_NAME}:${IMAGE_VERSION} --build-arg NORMAL_USER=${NORMAL_USER} --build-arg NORMAL_PASSWD=${NORMAL_PASSWD} --build-arg ROOT_PASSWD=${ROOT_PASSWD} -f dockerfile_ubuntu .
```

## run
#### centos
```shell
docker exec -it `docker run -d --name ${CONTAINER_NAME} -e HOST_USER -e HOST_PASSWD -e COMPANY_USER -e COMPANY_PASSWD -e RELAY_ADDR --privileged=true ${USER_NAME}/${IMAGE_NAME}:${IMAGE_VERSION}` /bin/bash
```

#### ubuntu
```shell
docker run -it --name ${CONTAINER_NAME} -e HOST_USER -e HOST_PASSWD -e COMPANY_USER -e COMPANY_PASSWD -e RELAY_ADDR --privileged=true ${USER_NAME}/${IMAGE_NAME}:${IMAGE_VERSION} /bin/bash
```

## TODO
1. If you want to use tmux, need to invoke `tmux source ~/.tmux.conf` in command line and `<Ctrl-b>+I` in tmux after login with normal user;
2. You need to update your user_name and email of git in .gitconfig located `/home/${NORMAL_USER}/`;

## suggection
If you want to mount volumns on MacOS, use `mutagen` or `docker-sync` instead of `-v` args, like:
```shell
mutagen sync create --name ${SESSION_NAME} --symlink-mode=posix-raw ${CODE_PATH_ON_HOST} docker://${NORMAL_USER}@${CONTAINER_NAME}${CODE_PATH_ON_CONTAINER}
```
