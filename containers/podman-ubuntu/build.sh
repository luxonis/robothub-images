#!/bin/bash
set -ex

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
  --build-arg NETAVARK_VERSION=${NETAVARK_VERSION} \
  --build-arg AARDVARK_DNS_VERSION=${AARDVARK_DNS_VERSION} \
  -o "type=local,dest=$(pwd)/packages/netavark" \
  -t netavark-build \
  -f ./netavark/Dockerfile \
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

mkdir -p ./packages/crun
wget -O "$(pwd)/packages/crun/crun_${CRUN_VERSION}_x86_64" https://github.com/containers/crun/releases/download/${CRUN_VERSION}/crun-${CRUN_VERSION}-linux-amd64
wget -O "$(pwd)/packages/crun/crun_${CRUN_VERSION}_aarch64" https://github.com/containers/crun/releases/download/${CRUN_VERSION}/crun-${CRUN_VERSION}-linux-arm64
# DOCKER_BUILDKIT=1 docker buildx build \
#   --builder remotebuilder \
#   --platform linux/arm64/v8,linux/amd64 \
#   --build-arg GO_LANG_VERSION=${GO_LANG_VERSION} \
#   --build-arg RUNC_VERSION=${RUNC_VERSION} \
#   -o "type=local,dest=$(pwd)/packages/runc" \
#   -t runc-build \
#   -f ./runc/Dockerfile \
#   .

DOCKER_BUILDKIT=1 docker buildx build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg GO_LANG_VERSION=${GO_LANG_VERSION} \
  --build-arg PODMAN_VERSION=${PODMAN_VERSION} \
  -o "type=local,dest=$(pwd)/packages/podman" \
  -t podman-build \
  -f ./podman/Dockerfile \
  .