#!/bin/bash
set -Eeux

IMAGE_REF_NAME="robothub-app-v2"
if [[ "${GITHUB_REF_NAME}" == "develop" ]]; then
    IMAGE_REF_NAME="${IMAGE_REF_NAME}-dev"
elif [[ "${GITHUB_REF_NAME}" != "main" ]]; then
    exit 1
fi

BASE_AMD64_TAG="ghcr.io/luxonis/${IMAGE_REF_NAME}-amd64:${IMAGE_VERSION}"
BASE_ARM64_TAG="ghcr.io/luxonis/${IMAGE_REF_NAME}-arm64:${IMAGE_VERSION}"
BASE_TAG="ghcr.io/luxonis/${IMAGE_REF_NAME}:${IMAGE_VERSION}"

# Define suffixes
declare -a suffixes=(
    "core"
    "rvc2-minimal"
    "rvc2-regular"
    "rvc2-minimal-ros2humble"
    "rvc2-regular-ros2humble"
    "rvc3-minimal"
    "rvc3-regular"
    "rvc3-minimal-ros2humble"
    "rvc3-regular-ros2humble"
    "rvc3-builtin-app"
    "rae-provisioning-app"
)

# Make manifests
for suffix in "${suffixes[@]}"; do
    docker manifest create "${BASE_TAG}-${suffix}" \
        --amend "${BASE_AMD64_TAG}-${suffix}" \
        --amend "${BASE_ARM64_TAG}-${suffix}"
    docker manifest push "${BASE_TAG}-${suffix}"
done
