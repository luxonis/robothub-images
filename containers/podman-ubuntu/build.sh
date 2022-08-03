#!/bin/bash

GO_LANG_VERSION="1.17"

CONMON_VERSION="2.1.0"
CNI_PLUGINS_VERSION="1.1.1"
RUNC_VERSION="1.1.1"
PODMAN_VERSION="v4.1.1"

mkdir ./packages
mkdir ./packages/amd64
mkdir ./packages/arm64

DOCKER_BUILDKIT=1 docker buildx build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg GO_LANG_VERSION=${GO_LANG_VERSION} \
  --build-arg CONMON_VERSION=${CONMON_VERSION} \
  --load \
  -t conmon-build \
  -f ./conmon/Dockerfile \
  .

docker container create --platform linux/arm64/v8 --name conmon-arm64 conmon-build
docker cp conmon-arm64:/packages/* ./packages/arm64/
docker container rm conmon-arm64

docker container create --platform linux/amd64 --name conmon-amd64 conmon-build
docker cp conmon-amd64:/packages/* ./packages/amd64/
docker container rm conmon-amd64