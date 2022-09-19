#!/bin/bash
set -Eeux

TAG_SUFFIX=""

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

git clone --depth=1 --recurse-submodules --branch "${DEPTHAI_BRANCH}" https://github.com/luxonis/depthai-python.git .depthai
cd .depthai
DEPTHAI_VERSION=$(python3 -c 'import find_version as v; print(v.get_package_version()); exit(0);')
cd ..

BASE_PACKAGE="ghcr.io/luxonis/robothub-app"
BASE_TAG="${BASE_PACKAGE}:${IMAGE_VERSION}"

BASE_ALPINE_TAG="${BASE_TAG}-alpine3.16${TAG_SUFFIX}"
BASE_UBUNTU_TAG="${BASE_TAG}-ubuntu22.04${TAG_SUFFIX}"

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
  --label	"com.luxonis.rh.depthai.branch=${DEPTHAI_BRANCH}" \
  --label	"com.luxonis.rh.base=alpine" \
  --label	"org.opencontainers.image.url=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.documentation=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.source=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.version=${IMAGE_VERSION}" \
  --label	"org.opencontainers.image.vendor=Luxonis" \
  --label	"org.opencontainers.image.title=RobotHub Perception App Base" \
  --label "org.opencontainers.image.description=Based on: Alpine\nDepthAI branch: ${DEPTHAI_BRANCH}\nDepthAI version: ${DEPTHAI_VERSION}" \
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
  --label	"com.luxonis.rh.depthai.branch=${DEPTHAI_BRANCH}" \
  --label	"com.luxonis.rh.base=ubuntu" \
  --label	"org.opencontainers.image.url=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.documentation=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.source=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.version=${IMAGE_VERSION}" \
  --label	"org.opencontainers.image.vendor=Luxonis" \
  --label	"org.opencontainers.image.title=RobotHub Perception App Base" \
  --label "org.opencontainers.image.description=Based on: Ubuntu\nDepthAI branch: ${DEPTHAI_BRANCH}\nDepthAI version: ${DEPTHAI_VERSION}" \
  -t ${BASE_UBUNTU_TAG} \
  --push \
  --file ./robothub_sdk/docker/ubuntu/Dockerfile \
  ./robothub_sdk

echo "================================"
echo "Building ROS..."
echo "================================"

#ROS

ROS_GALACTIC_TAG="${BASE_TAG}-ros2galactic${TAG_SUFFIX}"

DOCKER_BUILDKIT=1 docker buildx \
  build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg "ROS_VERSION_TAG=galactic-ros-base-focal" \
  --build-arg "DEPTHAI_VERSION=v${DEPTHAI_VERSION}" \
  --label	"com.luxonis.rh.depthai=${DEPTHAI_VERSION}" \
  --label	"com.luxonis.rh.depthai.branch=${DEPTHAI_BRANCH}" \
  --label	"com.luxonis.rh.base=ros2/galactic" \
  --label	"org.opencontainers.image.url=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.documentation=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.source=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.version=${IMAGE_VERSION}" \
  --label	"org.opencontainers.image.vendor=Luxonis" \
  --label	"org.opencontainers.image.title=RobotHub Perception App Base" \
  --label "org.opencontainers.image.description=Based on: ROS-galactic/Ubuntu-20.04\nDepthAI branch: ${DEPTHAI_BRANCH}\nDepthAI version: ${DEPTHAI_VERSION}" \
  -t "${ROS_GALACTIC_TAG}" \
  --push \
  --file ./robothub_sdk/docker/ros/Dockerfile \
  ./robothub_sdk

ROS_FOXY_TAG="${BASE_TAG}-ros2foxy${TAG_SUFFIX}"

DOCKER_BUILDKIT=1 docker buildx \
  build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg "ROS_VERSION_TAG=foxy-ros-base-focal" \
  --build-arg "DEPTHAI_VERSION=v${DEPTHAI_VERSION}" \
  --label	"com.luxonis.rh.depthai=${DEPTHAI_VERSION}" \
  --label	"com.luxonis.rh.depthai.branch=${DEPTHAI_BRANCH}" \
  --label	"com.luxonis.rh.base=ros2/foxy" \
  --label	"org.opencontainers.image.url=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.documentation=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.source=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.version=${IMAGE_VERSION}" \
  --label	"org.opencontainers.image.vendor=Luxonis" \
  --label	"org.opencontainers.image.title=RobotHub Perception App Base" \
  --label "org.opencontainers.image.description=Based on: ROS-foxy/Ubuntu-20.04\nDepthAI branch: ${DEPTHAI_BRANCH}\nDepthAI version: ${DEPTHAI_VERSION}" \
  -t "${ROS_FOXY_TAG}" \
  --push \
  --file ./robothub_sdk/docker/ros/Dockerfile \
  ./robothub_sdk

  
ROS_HUMBLE_TAG="${BASE_TAG}-ros2humble${TAG_SUFFIX}"

DOCKER_BUILDKIT=1 docker buildx \
  build \
  --builder remotebuilder \
  --platform linux/arm64/v8,linux/amd64 \
  --build-arg "ROS_VERSION_TAG=humble-ros-base-jammy" \
  --build-arg "DEPTHAI_VERSION=v${DEPTHAI_VERSION}" \
  --label	"com.luxonis.rh.depthai=${DEPTHAI_VERSION}" \
  --label	"com.luxonis.rh.depthai.branch=${DEPTHAI_BRANCH}" \
  --label	"com.luxonis.rh.base=ros2/humble" \
  --label	"org.opencontainers.image.url=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.documentation=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.source=https://github.com/luxonis/robothub-sdk" \
  --label	"org.opencontainers.image.version=${IMAGE_VERSION}" \
  --label	"org.opencontainers.image.vendor=Luxonis" \
  --label	"org.opencontainers.image.title=RobotHub Perception App Base" \
  --label "org.opencontainers.image.description=Based on: ROS-humble/Ubuntu-22.04\nDepthAI branch: ${DEPTHAI_BRANCH}\nDepthAI version: ${DEPTHAI_VERSION}" \
  -t "${ROS_HUMBLE_TAG}" \
  --push \
  --file ./robothub_sdk/docker/ros/Dockerfile \
  ./robothub_sdk

echo "================================"
echo "All done!"
echo "================================"
