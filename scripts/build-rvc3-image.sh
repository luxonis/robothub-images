#!/bin/bash
set -Eeux

TAG_SUFFIX=""

DEPTHAI_BRANCH="rvc3_develop"

if [[ -n "${EXTERNAL_TRIGGER_REF}" ]]; then
  DEPTHAI_BRANCH="${EXTERNAL_TRIGGER_REF##*/}"
elif [[ -z "${DEPTHAI_BRANCH}" ]]; then
  DEPTHAI_BRANCH="main"
else
  TAG_SUFFIX="${TAG_SUFFIX}-custom"
fi

if [[ "$GITHUB_REF_NAME" != "main" ]]; then
  TAG_SUFFIX="${TAG_SUFFIX}-dev"
fi

IMAGE_VERSION=$(date +"%Y.%j.%H%M")

if [[ "$DEPTHAI_BRANCH" != "main" ]]; then
  DEPTHAI_VERSION=$DEPTHAI_BRANCH
else
  git clone --depth=1 --recurse-submodules --branch "${DEPTHAI_BRANCH}" https://github.com/luxonis/depthai-python.git .depthai
  cd .depthai
  DEPTHAI_VERSION=$(python3 -c 'import find_version as v; print(v.get_package_version()); exit(0);')
  DEPTHAI_VERSION="v"$DEPTHAI_VERSION
  cd ..
fi

BASE_PACKAGE="ghcr.io/luxonis/robothub-app-v2"
BASE_TAG="${BASE_PACKAGE}:${IMAGE_VERSION}"
BASE_RVC3_TAG="${BASE_TAG}-rvc3${TAG_SUFFIX}"
BASE_ROS2HUMBLE_RVC3_TAG="${BASE_TAG}-ros2humble-rvc3${TAG_SUFFIX}"

echo "================================"
echo "Building images..."
echo "DEPTHAI_VERSION=${DEPTHAI_VERSION}"
echo "================================"

echo "================================"
echo "Building minimal..."
echo "=> ${BASE_RVC3_TAG}"
echo "================================"
# Minimal
DOCKER_BUILDKIT=1 docker buildx \
  build \
  --builder remotebuilder \
  --platform linux/amd64,linux/arm64 \
  --label "com.luxonis.rh.depthai=${DEPTHAI_VERSION}" \
  --label "com.luxonis.rh.depthai.branch=${DEPTHAI_BRANCH}" \
  --label "com.luxonis.rh.base=python3.10-slim-bullseye" \
  --label "org.opencontainers.image.version=${IMAGE_VERSION}" \
  --label "org.opencontainers.image.vendor=Luxonis" \
  --label "org.opencontainers.image.title=RobotHub Perception RVC3 App Base" \
  --label "org.opencontainers.image.description=Based on: Ubuntu\nDepthAI branch: ${DEPTHAI_BRANCH}\nDepthAI version: ${DEPTHAI_VERSION}" \
  -t "${BASE_RVC3_TAG}" \
  --push \
  --provenance=false \
  --file ./docker_images/rvc3/Dockerfile \
  ./

echo "================================"
echo "Building ROS Humble..."
echo "=> ${BASE_ROS2HUMBLE_RVC3_TAG}"
echo "================================"
# Minimal
DOCKER_BUILDKIT=1 docker buildx \
  build \
  --builder remotebuilder \
  --platform linux/amd64,linux/arm64 \
  --label "com.luxonis.rh.depthai=${DEPTHAI_VERSION}" \
  --label "com.luxonis.rh.depthai.branch=${DEPTHAI_BRANCH}" \
  --label "com.luxonis.rh.base=ros:humble-ros-base" \
  --label "org.opencontainers.image.version=${IMAGE_VERSION}" \
  --label "org.opencontainers.image.vendor=Luxonis" \
  --label "org.opencontainers.image.title=RobotHub Perception ROS2 Humble RVC3 App Base" \
  --label "org.opencontainers.image.description=Based on: Ubuntu\nDepthAI branch: ${DEPTHAI_BRANCH}\nDepthAI version: ${DEPTHAI_VERSION}" \
  -t "${BASE_ROS2HUMBLE_RVC3_TAG}" \
  --push \
  --provenance=false \
  --file ./docker_images/ros/humble/rvc3/Dockerfile \
  ./

echo "================================"
echo "All done!"
echo "================================"
