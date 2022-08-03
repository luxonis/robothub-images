#!/bin/bash

GO_LANG_VERSION="1.17"

CONMON_VERSION="2.1.0"
CNI_PLUGINS_VERSION="1.1.1"
RUNC_VERSION="1.1.1"
PODMAN_VERSION="v4.1.1"

mkdir ./packages

mkdir ./packages/conmon

DOCKER_BUILDKIT=1 docker buildx build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg GO_LANG_VERSION=${GO_LANG_VERSION} \
  --build-arg CONMON_VERSION=${CONMON_VERSION} \
  --output="type=local,dest=$(pwd)/packages/conmon" \
  -t conmon-build \
  -f ./conmon/Dockerfile \
  .