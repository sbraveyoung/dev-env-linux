# dev-env-linux
My development environment based on docker.

## build

#### environments
You shoul prepare those environments first:
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
1. You need to update your user_name and email of git in .gitconfig located `/home/${NORMAL_USER}/`;
2. If you want to use vim, need to invoke `vim +PlugInstall +qall` after login with normal user;
3. If you want to use tmux, need to invoke `tmux source ~/.tmux.conf` after login with normal user;

## suggection
If you want to mount volumns on MacOS, use `mutagen` or `docker-sync` instead of `-v` args.
