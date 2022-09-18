#!/bin/bash
set -Eeux

if [[ -z "${DEPTHAI_BRANCH}" ]]; then
  DEPTHAI_BRANCH="main"
fi

if [[ -n "${EXTERNAL_TRIGGER_REF}" ]]; then
  DEPTHAI_BRANCH="${EXTERNAL_TRIGGER_REF##*/}"
fi

TAG_SUFFIX=""
if [[ "$GITHUB_REF_NAME" != "main" ]]; then
  TAG_SUFFIX="-unstable"
fi

IMAGE_VERSION=$(date +"%Y.%j.%H%M")

git clone --depth=1 --recurse-submodules --branch "${DEPTHAI_BRANCH}" https://github.com/luxonis/depthai-python.git .depthai
cd .depthai
DEPTHAI_VERSION=$(python3 -c 'import find_version as v; print(v.get_package_version()); exit(0);')
cd ..

BASE_PACKAGE="ghcr.io/luxonis/robothub-app"
BASE_TAG="${BASE_PACKAGE}:${IMAGE_VERSION}"

BASE_ALPINE_TAG="${BASE_TAG}-alpine${TAG_SUFFIX}"
BASE_UBUNTU_TAG="${BASE_TAG}-ubuntu${TAG_SUFFIX}"

echo "================================"
echo "Building images..."
echo "DEPTHAI_VERSION=${DEPTHAI_VERSION}"
echo "================================"

echo "================================"
echo "Building alpine..."
echo "=> ${BASE_ALPINE_TAG}"
echo "================================"
# Alpine
DOCKER_BUILDKIT=1 docker buildx \
  build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg "DEPTHAI_VERSION=v${DEPTHAI_VERSION}" \
  --label	"com.luxonis.rh.depthai=${DEPTHAI_VERSION}" \
  --label	"com.luxonis.rh.base=alpine" \
  -t ${BASE_ALPINE_TAG} \
  --push \
  --file ./robothub_sdk/docker/alpine/Dockerfile \
  ./robothub_sdk

echo "================================"
echo "Building ubuntu..."
echo "=> ${BASE_UBUNTU_TAG}"
echo "================================"
#Ubuntu
DOCKER_BUILDKIT=1 docker buildx \
  build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg "DEPTHAI_VERSION=v${DEPTHAI_VERSION}" \
  --label	"com.luxonis.rh.depthai=${DEPTHAI_VERSION}" \
  --label	"com.luxonis.rh.base=ubuntu" \
  -t ${BASE_UBUNTU_TAG} \
  --push \
  --file ./robothub_sdk/docker/ubuntu/Dockerfile \
  ./robothub_sdk

echo "================================"
echo "All done!"
echo "================================"
