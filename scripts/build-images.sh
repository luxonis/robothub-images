#!/bin/bash
set -Eeux

export IMAGE_REF_NAME="robothub-app-v2"
if [[ "${GITHUB_REF_NAME}" == "develop" ]]; then
    IMAGE_REF_NAME="${IMAGE_REF_NAME}-dev"
elif [[ "${GITHUB_REF_NAME}" != "main" ]]; then
    exit 1
fi

export BASE_PACKAGE="ghcr.io/luxonis/${IMAGE_REF_NAME}"
export IMAGE_VERSION=$(date +"%Y.%j.%H%M")
export BASE_TAG="${BASE_PACKAGE}:${IMAGE_VERSION}"
export DOCKER_BUILDKIT=1

./scripts/build-images-base.sh
./scripts/build-images-custom.sh
