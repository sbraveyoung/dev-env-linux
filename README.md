# dev-env-linux
A modern linux development environment based on docker, inspired by [modern-unix](https://github.com/ibraheemdev/modern-unix), more than it.

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
docker exec -it `docker run -d --name ${CONTAINER_NAME} --privileged=true ${USER_NAME}/${IMAGE_NAME}:${IMAGE_VERSION}` /bin/bash
```

#### ubuntu
```shell
docker run -it --name ${CONTAINER_NAME} --privileged=true ${USER_NAME}/${IMAGE_NAME}:${IMAGE_VERSION} /bin/bash
```

## TODO
1. If you want to use vim, need to invoke `vim +PlugInstall +qall` after login with normal user;
2. If you are a Go developer, need to invoke `vim +GoInstallBinaries +qall` after login with ROOT user;
3. If you want to use tmux, need to invoke `tmux source ~/.tmux.conf` after login with normal user;
4. You need to update your user_name and email of git in .gitconfig located `/home/${NORMAL_USER}/`;

## suggection
If you want to mount volumns on MacOS, use `mutagen` or `docker-sync` instead of `-v` args, like:
```shell
mutagen sync create --name ${SESSION_NAME} --symlink-mode=posix-raw ${CODE_PATH_ON_HOST} docker://${NORMAL_USER}@${CONTAINER_NAME}${CODE_PATH_ON_CONTAINER}
```
