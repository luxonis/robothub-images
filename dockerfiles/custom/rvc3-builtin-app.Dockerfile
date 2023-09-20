FROM ubuntu:22.04 AS base

ARG DEBIAN_FRONTEND=noninteractive

ENV PYTHONPATH=/lib \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install python3
RUN apt-get update -qq && \
    apt-get install -qq --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/* && \
    python3 -m pip install --upgrade pip setuptools wheel

FROM base AS build

ARG TARGETARCH
ARG DEPTHAI_VERSION

# Install depthai
COPY libusb-1.0-${TARGETARCH}.so /lib/libusb-1.0.so
COPY install-depthai-version /usr/local/bin
RUN install-depthai-version ${DEPTHAI_VERSION}

FROM base

# Copy python3 packages
COPY --from=build /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
