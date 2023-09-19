#!/bin/bash
set -Eeux

declare -a elems=(
    "rvc2 ubuntu:22.04 minimal"
    "rvc2 ubuntu:22.04 regular"
    "rvc2 ros:humble-ros-core minimal"
    "rvc2 ros:humble-ros-base regular"
    "rvc3 ubuntu:22.04 minimal"
    "rvc3 ubuntu:22.04 regular"
    "rvc3 ros:humble-ros-core minimal"
    "rvc3 ros:humble-ros-base regular"
)

for elem in "${elems[@]}"; do
    # Define base parameters
    read -a strarr <<<"$elem"
    ROBOTICS_VISION_CORE=${strarr[0]}
    BASE_IMAGE=${strarr[1]}
    VARIANT=${strarr[2]}

    # Derive remaining parameters
    DEPTHAI_VERSION=""
    if [[ "${ROBOTICS_VISION_CORE}" == "rvc2" ]]; then
        DEPTHAI_VERSION="2.22.0.0"
    elif [[ "${ROBOTICS_VISION_CORE}" == "rvc3" ]]; then
        DEPTHAI_VERSION="2.22.0.0.dev0+8b9eceb316ce60d57d9157ecec48534b548e8904"
    else
        echo "Unknown ROBOTICS_VISION_CORE: ${ROBOTICS_VISION_CORE}"
        continue
    fi

    TAG="${BASE_TAG}-${ROBOTICS_VISION_CORE}-${VARIANT}"
    if [[ "${BASE_IMAGE}" == "ros:humble-ros-core" || "${BASE_IMAGE}" == "ros:humble-ros-base" ]]; then
        TAG="${TAG}-ros2humble"
    fi

    # Build
    echo "================================"
    echo "Building '${TAG}'..."
    echo "=> Depthai version: ${DEPTHAI_VERSION}"
    echo "================================"

    docker buildx build \
        --builder remotebuilder \
        --platform linux/amd64,linux/arm64 \
        --build-arg "BASE_IMAGE=ubuntu:22.04" \
        --build-arg "ROBOTICS_VISION_CORE=${ROBOTICS_VISION_CORE}" \
        --build-arg "DEPTHAI_VERSION=${DEPTHAI_VERSION}" \
        --build-arg "VARIANT=${VARIANT}" \
        --label "org.opencontainers.image.source=https://github.com/luxonis/robothub-images" \
        --label "org.opencontainers.image.version=${IMAGE_VERSION}" \
        --label "org.opencontainers.image.vendor=Luxonis" \
        --label "org.opencontainers.image.ref.name=${IMAGE_REF_NAME}" \
        --label "org.opencontainers.image.title=RobotHub App base image" \
        --label "org.opencontainers.image.description=DepthAI version: ${DEPTHAI_VERSION}" \
        --label "com.luxonis.rh.depthai.version=${DEPTHAI_VERSION}" \
        --tag "${TAG}" \
        --push \
        --provenance=false \
        --file dockerfiles/base.Dockerfile \
        context/
done
