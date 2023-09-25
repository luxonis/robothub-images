#!/bin/bash
set -Eeux

CORE_TAG="${BASE_TAG}-core"
echo "================================"
echo "Building '${CORE_TAG}'..."
echo "================================"
docker buildx build \
    --label "org.opencontainers.image.source=https://github.com/luxonis/robothub-images" \
    --label "org.opencontainers.image.version=${IMAGE_VERSION}" \
    --label "org.opencontainers.image.vendor=Luxonis" \
    --label "org.opencontainers.image.ref.name=${IMAGE_REF_NAME}" \
    --label "org.opencontainers.image.title=RobotHub App core image" \
    --tag "${CORE_TAG}" \
    --push \
    --provenance=false \
    --file dockerfiles/core.Dockerfile \
    context/
