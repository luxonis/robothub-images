#!/bin/bash

TARGETARCH_LINUX=""
if [[ "${TARGETARCH}" == "amd64" ]]; then
    TARGETARCH_LINUX="x86_64"
elif [[ "${TARGETARCH}" == "arm64" ]]; then
    TARGETARCH_LINUX="aarch64"
else
    echo "Unknown TARGETARCH: ${TARGETARCH}"
    exit 1
fi

wget -O /lib/libusb-1.0.so "https://rh-public.luxonis.com/libusb/1.0.26/libusb-${TARGETARCH_LINUX}.so"
