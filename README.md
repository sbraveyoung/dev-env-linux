# dev-env-linux
My development environment based on docker.

## build
```shell
export USER_NAME=your_user
export IMAGE_NAME=image_name_you_want
export IMAGE_VERSION=image_version_you_want
export NORMAL_USER=normal_user_name_you_want
export NORMAL_PASSED=normal_user_password_you_want
export ROOT_PASSWD=root_password_you_want

#centos
docker build -t ${USER_NAME}/${IMAGE_NAME}:${IMAGE_VERSION} --build-arg NORMAL_USER=${NORMAL_USER} --build-arg NORMAL_PASSWD=${NORMAL_PASSWD} --build-arg ROOT_PASSWD=${ROOT_PASSWD} -f dockerfile_centos .

#ubuntu
docker build -t ${USER_NAME}/${IMAGE_NAME}:${IMAGE_VERSION} --build-arg NORMAL_USER=${NORMAL_USER} --build-arg NORMAL_PASSWD=${NORMAL_PASSWD} --build-arg ROOT_PASSWD=${ROOT_PASSWD} -f dockerfile_ubuntu .
```

## run
```shell
export CONTAINER_NAME=dev-linux-env #or any name you want

#centos
docker exec -it `docker run -d --name ${CONTAINER_NAME} --privileged=true ${USER_NAME}/${IMAGE_NAME}:${IMAGE_VERSION}` /bin/bash

#ubuntu
docker run -it --name ${CONTAINER_NAME} --privileged=true ${USER_NAME}/${IMAGE_NAME}:${IMAGE_VERSION} /bin/bash
```

## suggection
If you want to mount volumns on MacOS, use `mutagen` or `docker-sync` instead of `-v` args.
