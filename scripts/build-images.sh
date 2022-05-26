#!/bin/bash
set -Eeuo pipefail

if [[ -z "${DEPTHAI_BRANCH}" ]]; then
  DEPTHAI_BRANCH="main"
fi

commitSuffix=""
if [[ "$GITHUB_REF_NAME" != "main" ]]; then
  if [[ "$GITHUB_REF_NAME" == "develop" ]]; then
    commitSuffix="-develop"
  else
    commitSuffix="-${GITHUB_SHA}"
  fi
fi

ALPINE_TAG="ghcr.io/luxonis/robothub-base-app:alpine-depthai-${DEPTHAI_BRANCH}${commitSuffix}"
UBUNTU_TAG="ghcr.io/luxonis/robothub-base-app:ubuntu-depthai-${DEPTHAI_BRANCH}${commitSuffix}"
LATEST_TAG="ghcr.io/luxonis/robothub-base-app:latest"

echo "Building alpine..."
# Alpine
DOCKER_BUILDKIT=1 docker buildx \
  build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg DEPTHAI_BRANCH=${DEPTHAI_BRANCH} \
  -t $ALPINE_TAG \
  --push \
  --file ./robothub_sdk/docker/alpine/Dockerfile \
  ./robothub_sdk

echo "Building ubuntu..."
#Ubuntu
DOCKER_BUILDKIT=1 docker buildx \
  build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg DEPTHAI_BRANCH=${DEPTHAI_BRANCH} \
  -t $UBUNTU_TAG \
  --push \
  --file ./robothub_sdk/docker/ubuntu/Dockerfile \
  ./robothub_sdk

if [[ "${DEPTHAI_BRANCH}" == "main" && "${GITHUB_REF_NAME}" == "main" ]]; then
  docker tag "$ALPINE_TAG" "$LATEST_TAG"
  docker push "$LATEST_TAG"
fi