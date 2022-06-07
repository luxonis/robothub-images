#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_PATH=$(realpath "$0")
ROOT_DIR=$(dirname "$(dirname "$SCRIPT_PATH")")

DEPTHAI_BRANCH="main"

imageSuffix="-local"
cacheSuffix="-local-buildcache"

ALPINE_TAG="ghcr.io/luxonis/robothub-base-app:alpine-depthai-${DEPTHAI_BRANCH}${imageSuffix}"
ALPINE_CACHE_TAG="ghcr.io/luxonis/robothub-base-app:alpine-${DEPTHAI_BRANCH}${cacheSuffix}"
UBUNTU_TAG="ghcr.io/luxonis/robothub-base-app:ubuntu-depthai-${DEPTHAI_BRANCH}${imageSuffix}"
UBUNTU_CACHE_TAG="ghcr.io/luxonis/robothub-base-app:ubuntu-${DEPTHAI_BRANCH}${cacheSuffix}"

echo "Building alpine..."
# Alpine
DOCKER_BUILDKIT=1 docker buildx \
  build \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg DEPTHAI_BRANCH=${DEPTHAI_BRANCH} \
  --cache-to type=registry,ref="${ALPINE_CACHE_TAG}" \
  --cache-from type=registry,ref="${ALPINE_CACHE_TAG}" \
  -t $ALPINE_TAG \
  --push \
  --file "${ROOT_DIR}"/robothub_sdk/docker/alpine/Dockerfile \
  "${ROOT_DIR}"/robothub_sdk

echo "Building ubuntu..."
#Ubuntu
DOCKER_BUILDKIT=1 docker buildx \
  build \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg DEPTHAI_BRANCH=${DEPTHAI_BRANCH} \
  --cache-to type=registry,ref="${UBUNTU_CACHE_TAG}" \
  --cache-from type=registry,ref="${UBUNTU_CACHE_TAG}" \
  -t $UBUNTU_TAG \
  --push \
  --file "${ROOT_DIR}"/robothub_sdk/docker/ubuntu/Dockerfile \
  "${ROOT_DIR}"/robothub_sdk
