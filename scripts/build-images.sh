#!/bin/bash
set -Eeux

export BASE_PACKAGE="ghcr.io/luxonis/${IMAGE_REF_NAME}-${ARCH}"
export BASE_TAG="${BASE_PACKAGE}:${IMAGE_VERSION}"
export DOCKER_BUILDKIT=1

./scripts/build-images-core.sh
./scripts/build-images-base.sh
./scripts/build-images-custom.sh
