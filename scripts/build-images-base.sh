#!/bin/bash
set -Eeux

declare -A versions
CONFIG_FILE="scripts/versions.conf"
if [ ! -f "${CONFIG_FILE}" ]; then
    echo "The file ${CONFIG_FILE} does not exist."
    exit 1
fi

echo "Reading versions from ${CONFIG_FILE}..."
while IFS='=' read -r key value; do
    versions[$key]=$value
done < "${CONFIG_FILE}"

# Define base parameters
ROBOTHUB_VERSION="2.4.0"

build_and_push_image() {
    local robotics_vision_core=$1
    local base_image=$2
    local variant=$3
    local dockerfile=$4

    IFS=',' read -r depthai_version depthai_sdk_version <<< "${versions[${robotics_vision_core}]}"
    if [ -z "${depthai_version}" ]; then
        echo "No version found for ${robotics_vision_core} in ${CONFIG_FILE}"
        return
    fi

    local tag="${BASE_TAG}-${robotics_vision_core}-${variant}"
    if [[ "${base_image}" == "ros:humble-ros-core" || "${base_image}" == "ros:humble-ros-base" ]]; then
        tag="${tag}-ros2humble"
    fi

    echo "================================"
    echo "Building '${tag}'..."
    echo "=> Depthai version: ${depthai_version}"
    echo "=> Depthai SDK version: ${depthai_sdk_version}"
    echo "=> RobotHub version: ${ROBOTHUB_VERSION}"
    echo "================================"

    LABELS=(
        "--label" "org.opencontainers.image.source=https://github.com/luxonis/robothub-images"
        "--label" "org.opencontainers.image.version=${tag}"
        "--label" "org.opencontainers.image.vendor=Luxonis"
        "--label" "org.opencontainers.image.ref.name=${IMAGE_REF_NAME}"
        "--label" "org.opencontainers.image.title=RobotHub App base image"
        "--label" "org.opencontainers.image.description=DepthAI version: ${depthai_version}"
        "--label" "com.luxonis.rh.depthai.version=${depthai_version}"
        "--label" "com.luxonis.rh.robothub.version=${ROBOTHUB_VERSION}"
    )

    BUILD_ARGS=(
        "--build-arg" "BASE_IMAGE=${base_image}"
        "--build-arg" "ROBOTICS_VISION_CORE=${robotics_vision_core}"
        "--build-arg" "DEPTHAI_SDK_VERSION=${depthai_sdk_version}"
        "--build-arg" "DEPTHAI_VERSION=${depthai_version}"
        "--build-arg" "ROBOTHUB_VERSION=${ROBOTHUB_VERSION}"
        "--build-arg" "VARIANT=${variant}"
    )

    # Check if the Robotics Vision Core version is not rvc2-depthaiV3
    if [[ "${robotics_vision_core}" != "rvc2-depthaiV3" ]]; then
        LABELS+=("--label" "com.luxonis.rh.depthai-sdk.version=${depthai_sdk_version}")
    fi

    docker buildx build \
    "${BUILD_ARGS[@]}" \
    "${LABELS[@]}" \
    --tag "${tag}" \
    --push \
    --provenance=false \
    --file "dockerfiles/${dockerfile}" \
    context/
}

# Define base parameters
BASE_DOCKERFILE="base.Dockerfile"
DEPTHAI_V3_DOCKERFILE_CONTEXT="depthai-v3-git"

declare -a elems=(
    # RVC2 - DepthAI from registry:
    "rvc2 ubuntu:22.04 minimal ${BASE_DOCKERFILE}"
    "rvc2 ubuntu:22.04 regular ${BASE_DOCKERFILE}"
    "rvc2 ros:humble-ros-core minimal ${BASE_DOCKERFILE}"
    "rvc2 ros:humble-ros-base regular ${BASE_DOCKERFILE}"

    # RVC3 - DepthAI from registry:
    "rvc3 ubuntu:22.04 minimal ${BASE_DOCKERFILE}"
    "rvc3 ubuntu:22.04 regular ${BASE_DOCKERFILE}"
    "rvc3 ros:humble-ros-core minimal ${BASE_DOCKERFILE}"
    "rvc3 ros:humble-ros-base regular ${BASE_DOCKERFILE}"

    # RVC2 - DepthAI V3 - built from source:
    "rvc2-depthaiV3 ubuntu:22.04 minimal ${DEPTHAI_V3_DOCKERFILE_CONTEXT}/${BASE_DOCKERFILE}"
    "rvc2-depthaiV3 ubuntu:22.04 regular ${DEPTHAI_V3_DOCKERFILE_CONTEXT}/${BASE_DOCKERFILE}"
    "rvc2-depthaiV3 ros:humble-ros-core minimal ${DEPTHAI_V3_DOCKERFILE_CONTEXT}/${BASE_DOCKERFILE}"
    "rvc2-depthaiV3 ros:humble-ros-base regular ${DEPTHAI_V3_DOCKERFILE_CONTEXT}/${BASE_DOCKERFILE}"
)

for elem in "${elems[@]}"; do
    read -ra strarr <<<"$elem"
    build_and_push_image "${strarr[0]}" "${strarr[1]}" "${strarr[2]}" "${strarr[3]}"
done
