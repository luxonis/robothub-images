#!/bin/bash
set -Eeux

DEPTHAI_VERSION="2.22.0.0.dev0+8b9eceb316ce60d57d9157ecec48534b548e8904"

RVC3_BUILTIN_APP_TAG="${BASE_TAG}-rvc3-builtin-app"
echo "================================"
echo "Building '${RVC3_BUILTIN_APP_TAG}'..."
echo "=> Depthai version: ${DEPTHAI_VERSION}"
echo "================================"
docker buildx build \
    --builder remotebuilder \
    --platform linux/amd64,linux/arm64 \
    --build-arg "DEPTHAI_VERSION=${DEPTHAI_VERSION}" \
    --label "org.opencontainers.image.source=https://github.com/luxonis/robothub-images" \
    --label "org.opencontainers.image.version=${IMAGE_VERSION}" \
    --label "org.opencontainers.image.vendor=Luxonis" \
    --label "org.opencontainers.image.ref.name=${IMAGE_REF_NAME}" \
    --label "org.opencontainers.image.title=RobotHub RVC3 builtin app image" \
    --label "org.opencontainers.image.description=DepthAI version: ${DEPTHAI_VERSION}" \
    --label "com.luxonis.rh.depthai.version=${DEPTHAI_VERSION}" \
    --tag "${RVC3_BUILTIN_APP_TAG}" \
    --push \
    --provenance=false \
    --file dockerfiles/custom/rvc3-builtin-app.Dockerfile \
    context/

RAE_PROVISIONING_APP_TAG="${BASE_TAG}-rae-provisioning-app"
echo "================================"
echo "Building '${RAE_PROVISIONING_APP_TAG}'..."
echo "=> Depthai version: ${DEPTHAI_VERSION}"
echo "================================"
docker buildx build \
    --builder remotebuilder \
    --platform linux/amd64,linux/arm64 \
    --build-arg "DEPTHAI_VERSION=${DEPTHAI_VERSION}" \
    --label "org.opencontainers.image.source=https://github.com/luxonis/robothub-images" \
    --label "org.opencontainers.image.version=${IMAGE_VERSION}" \
    --label "org.opencontainers.image.vendor=Luxonis" \
    --label "org.opencontainers.image.ref.name=${IMAGE_REF_NAME}" \
    --label "org.opencontainers.image.title=RobotHub RAE provisioning app image" \
    --label "org.opencontainers.image.description=DepthAI version: ${DEPTHAI_VERSION}" \
    --label "com.luxonis.rh.depthai.version=${DEPTHAI_VERSION}" \
    --tag "${RAE_PROVISIONING_APP_TAG}" \
    --push \
    --provenance=false \
    --file dockerfiles/custom/rae-provisioning-app.Dockerfile \
    context/
