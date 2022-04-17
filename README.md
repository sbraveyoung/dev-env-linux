# dev-env-linux
My development environment based on docker.

## build
```shell
docker build -t ${USER_NAME}/${IMAGE_NAME}:${VERSION} --build-arg NORMAL_USER=${NORMAL_USER} --build-arg NORMAL_PASSWD=${NORMAL_PASSWD} --build-arg ROOT_PASSWD=${ROOT_PASSWD} .
```

## run
```shell
#ubuntu(recommend)
docker run -it --name ${dev-linux-env} --privileged=true ${USER_NAME}/${IMAGE_NAME}:${VERSION} /bin/bash

#centos(deprecated)
git checkout dockerfile_centos_based
docker exec -it `docker run -d --name ${dev-linux-env} --privileged=true ${USER_NAME}/${IMAGE_NAME}:${VERSION}` /bin/bash
```

## suggection
If you want to mount volumns on MacOS, use `mutagen` or `docker-sync` instead of `-v` args.
