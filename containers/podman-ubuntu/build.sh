#!/bin/bash
set -ex

GO_LANG_VERSION="1.17"

CONMON_VERSION="2.1.0"
CNI_PLUGINS_VERSION="1.1.1"
RUNC_VERSION="1.1.1"
PODMAN_VERSION="4.1.1"

cd ./containers/podman-ubuntu


mkdir -p ./packages/conmon

DOCKER_BUILDKIT=1 docker buildx build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg GO_LANG_VERSION=${GO_LANG_VERSION} \
  --build-arg CONMON_VERSION=${CONMON_VERSION} \
  -o "type=local,dest=$(pwd)/packages/conmon" \
  -t conmon-build \
  -f ./conmon/Dockerfile \
  .

DOCKER_BUILDKIT=1 docker buildx build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg GO_LANG_VERSION=${GO_LANG_VERSION} \
  --build-arg CNI_PLUGINS_VERSION=${CNI_PLUGINS_VERSION} \
  -o "type=local,dest=$(pwd)/packages/cni-plugins" \
  -t cni-build \
  -f ./cni-plugins/Dockerfile \
  .

DOCKER_BUILDKIT=1 docker buildx build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg GO_LANG_VERSION=${GO_LANG_VERSION} \
  --build-arg RUNC_VERSION=${RUNC_VERSION} \
  -o "type=local,dest=$(pwd)/packages/runc" \
  -t runc-build \
  -f ./runc/Dockerfile \
  .

DOCKER_BUILDKIT=1 docker buildx build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg GO_LANG_VERSION=${GO_LANG_VERSION} \
  --build-arg PODMAN_VERSION=${PODMAN_VERSION} \
  -o "type=local,dest=$(pwd)/packages/podman" \
  -t podman-build \
  -f ./podman/Dockerfile \
  .