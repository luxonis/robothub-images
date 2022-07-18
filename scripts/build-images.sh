#!/bin/bash
set -Eeuo pipefail

# NOTE(michal): Change this if you want to temporarily change main branch for an unreleased version
DEPTHAI_MAIN_BRANCH="power_cycle_stuck_fix"

if [[ -z "${DEPTHAI_BRANCH}" ]]; then
  DEPTHAI_BRANCH="main"
fi

if [[ -n "${EXTERNAL_TRIGGER_REF}" ]]; then
  DEPTHAI_BRANCH="${EXTERNAL_TRIGGER_REF##*/}"
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
ALPINE_CACHE_TAG="ghcr.io/luxonis/robothub-base-app:alpine-${DEPTHAI_BRANCH}${cacheSuffix}"

ALPINE_DEV_TAG="ghcr.io/luxonis/robothub-dev-app:alpine-depthai-${DEPTHAI_BRANCH}${imageSuffix}"
ALPINE_CACHE_DEV_TAG="ghcr.io/luxonis/robothub-dev-app:alpine-${DEPTHAI_BRANCH}${cacheSuffix}"

UBUNTU_TAG="ghcr.io/luxonis/robothub-base-app:ubuntu-depthai-${DEPTHAI_BRANCH}${imageSuffix}"
UBUNTU_CACHE_TAG="ghcr.io/luxonis/robothub-base-app:ubuntu-${DEPTHAI_BRANCH}${cacheSuffix}"
LATEST_TAG="ghcr.io/luxonis/robothub-base-app:latest"

if [[ "${DEPTHAI_BRANCH}" == "main" ]]; then
  DEPTHAI_BRANCH="${DEPTHAI_MAIN_BRANCH}"
fi

echo "================================"
echo "Building images..."
echo "DEPTHAI_BRANCH=${DEPTHAI_BRANCH}"
echo "IMAGE_SUFFIX=${imageSuffix}"
echo "CACHE_SUFFIX=${cacheSuffix}"
echo "================================"

echo "================================"
echo "Building alpine..."
echo "=> ${ALPINE_TAG}"
echo "================================"
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

if [[ "${DEPTHAI_BRANCH}" == "${DEPTHAI_MAIN_BRANCH}" && "${GITHUB_REF_NAME}" == "main" ]]; then
  echo "================================"
  echo "Pushing as latest"
  echo "=> ${LATEST_TAG}"
  echo "================================"
  docker pull "$ALPINE_TAG"
  docker tag "$ALPINE_TAG" "$LATEST_TAG"
  docker push "$LATEST_TAG"
fi

echo "================================"
echo "Building alpine (dev)..."
echo "=> ${ALPINE_DEV_TAG}"
echo "================================"
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

echo "================================"
echo "Building ubuntu..."
echo "=> ${UBUNTU_TAG}"
echo "================================"
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

echo "================================"
echo "All done!"
echo "================================"