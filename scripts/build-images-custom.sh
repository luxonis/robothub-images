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


build_and_push_image() {
    local version_key=$1
    local tag_suffix=$2
    local dockerfile=$3

    IFS=',' read -r depthai_version _ <<< "${versions[${version_key}]}"

    if [ -z "${depthai_version}" ]; then
        echo "No version found for ${version_key} in ${CONFIG_FILE}"
        return
    fi

    local tag="${BASE_TAG}-${tag_suffix}"
    echo "================================"
    echo "Building '${tag}'..."
    echo "=> Depthai version: ${depthai_version}"
    echo "================================"

    docker buildx build \
        --build-arg "DEPTHAI_VERSION=${depthai_version}" \
        --label "org.opencontainers.image.source=https://github.com/luxonis/robothub-images" \
        --label "org.opencontainers.image.version=${IMAGE_VERSION}" \
        --label "org.opencontainers.image.vendor=Luxonis" \
        --label "org.opencontainers.image.ref.name=${IMAGE_REF_NAME}" \
        --label "org.opencontainers.image.title=RobotHub ${tag_suffix} image" \
        --label "org.opencontainers.image.description=DepthAI version: ${depthai_version}" \
        --label "com.luxonis.rh.depthai.version=${depthai_version}" \
        --tag "${tag}" \
        --push \
        --provenance=false \
        --file "dockerfiles/${dockerfile}" \
        context/
}

BASE_DOCKERFILE="builtin-app.Dockerfile"
CUSTOM_DOCKERFILE_CONTEXT="custom"
build_and_push_image "rvc2" "rvc2-builtin-app" "${CUSTOM_DOCKERFILE_CONTEXT}/${BASE_DOCKERFILE}"
build_and_push_image "rvc3" "rvc3-builtin-app" "${CUSTOM_DOCKERFILE_CONTEXT}/${BASE_DOCKERFILE}"
build_and_push_image "rvc3" "rae-provisioning-app" "${CUSTOM_DOCKERFILE_CONTEXT}/rae-provisioning-app.Dockerfile"

# Build images for RVC2 DepthAI V3:
build_and_push_image "rvc2-depthaiV3" "rvc2-depthaiV3-builtin-app" "depthai-v3-git/${BASE_DOCKERFILE}"
