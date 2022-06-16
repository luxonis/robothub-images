#!/bin/bash
set -Eeuo pipefail

if [[ -z "${DEPTHAI_BRANCH}" ]]; then
  DEPTHAI_BRANCH="main"
fi

imageSuffix=""
cacheSuffix="-buildcache"
if [[ "$GITHUB_REF_NAME" != "main" ]]; then
  cacheSuffix="-last-buildcache"
  if [[ "$GITHUB_REF_NAME" == "develop" ]]; then
    cacheSuffix="-develop-buildcache"
    imageSuffix="-develop"
  else
    imageSuffix="-${GITHUB_SHA}"
  fi
fi

ALPINE_TAG="ghcr.io/luxonis/robothub-base-app:alpine-depthai-${DEPTHAI_BRANCH}${imageSuffix}"
ALPINE_DEV_TAG="ghcr.io/luxonis/robothub-dev-app:alpine-depthai-${DEPTHAI_BRANCH}${imageSuffix}"
ALPINE_CACHE_TAG="ghcr.io/luxonis/robothub-base-app:alpine-${DEPTHAI_BRANCH}${cacheSuffix}"
ALPINE_CACHE_DEV_TAG="ghcr.io/luxonis/robothub-dev-app:alpine-${DEPTHAI_BRANCH}${cacheSuffix}"
UBUNTU_TAG="ghcr.io/luxonis/robothub-base-app:ubuntu-depthai-${DEPTHAI_BRANCH}${imageSuffix}"
UBUNTU_CACHE_TAG="ghcr.io/luxonis/robothub-base-app:ubuntu-${DEPTHAI_BRANCH}${cacheSuffix}"
LATEST_TAG="ghcr.io/luxonis/robothub-base-app:latest"

echo "Building alpine..."
# Alpine
DOCKER_BUILDKIT=1 docker buildx \
  build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg DEPTHAI_BRANCH=${DEPTHAI_BRANCH} \
  --cache-to type=registry,ref="${ALPINE_CACHE_TAG}" \
  --cache-from type=registry,ref="${ALPINE_CACHE_TAG}" \
  -t $ALPINE_TAG \
  --push \
  --file ./robothub_sdk/docker/alpine/Dockerfile \
  ./robothub_sdk

# Alpine Dev
DOCKER_BUILDKIT=1 docker buildx \
  build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg FROM_IMAGE_TAG=${ALPINE_TAG} \
  --build-arg DEPTHAI_BRANCH=${DEPTHAI_BRANCH} \
  --cache-to type=registry,ref="${ALPINE_CACHE_DEV_TAG}" \
  --cache-from type=registry,ref="${ALPINE_CACHE_DEV_TAG}" \
  -t "${ALPINE_DEV_TAG}" \
  --push \
  --file ./robothub_sdk/docker/alpine/Dockerfile.dev \
  ./robothub_sdk

echo "Building ubuntu..."
#Ubuntu
DOCKER_BUILDKIT=1 docker buildx \
  build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg DEPTHAI_BRANCH=${DEPTHAI_BRANCH} \
  --cache-to type=registry,ref="${UBUNTU_CACHE_TAG}" \
  --cache-from type=registry,ref="${UBUNTU_CACHE_TAG}" \
  -t $UBUNTU_TAG \
  --push \
  --file ./robothub_sdk/docker/ubuntu/Dockerfile \
  ./robothub_sdk

if [[ "${DEPTHAI_BRANCH}" == "main" && "${GITHUB_REF_NAME}" == "main" ]]; then
  docker tag "$ALPINE_TAG" "$LATEST_TAG"
  docker push "$LATEST_TAG"
fi