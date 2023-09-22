FROM ubuntu:22.04 AS base

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONPATH=/lib \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install python3
RUN apt-get update -qq && \
    apt-get install -qq --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

FROM base AS build

ARG DEBIAN_FRONTEND=noninteractive
ARG TARGETARCH

# Install dependencies
RUN apt-get update -qq  && \
    apt-get install -qq --no-install-recommends ca-certificates wget && \
    rm -rf /var/lib/apt/lists/*

# Download patched libusb
COPY download-patched-libusb /tmp/
RUN /tmp/download-patched-libusb ${TARGETARCH}

FROM base

# Copy libusb and scripts
COPY --from=build /lib/libusb-1.0.so /lib/libusb-1.0.so
COPY install-depthai-version /usr/local/bin
COPY install-luxonis-packages /usr/local/bin
