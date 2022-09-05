# syntax=docker/dockerfile:experimental
FROM alpine:3.16.0 as origin

# Python will buffer output in case of non interactive terminals and we don't want that, because it delays logs
ENV PYTHONPATH=/lib \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

FROM origin as base

ARG TARGETARCH
ARG DEPTHAI_BRANCH=main

RUN mkdir -p /var/cache/apk-$TARGETARCH && ln -s /var/cache/apk-$TARGETARCH /etc/apk/cache
RUN --mount=type=cache,mode=0777,id=apk-$TARGETARCH,target=/var/cache/apk-$TARGETARCH apk update && apk add python3 py3-numpy ca-certificates
RUN python3 -m ensurepip

FROM base as build

RUN --mount=type=cache,mode=0777,id=apk-$TARGETARCH,target=/var/cache/apk-$TARGETARCH apk update && apk add build-base python3-dev cmake linux-headers git wget
RUN wget https://github.com/libusb/libusb/releases/download/v1.0.25/libusb-1.0.25.tar.bz2 -O libusb.tar.bz2
RUN git clone --depth=1 --recurse-submodules --branch "${DEPTHAI_BRANCH}" https://github.com/luxonis/depthai-python.git

RUN tar xf libusb.tar.bz2 \
    && cd libusb-* \
    && ./configure --disable-udev \
    && make -j$(nproc) \
    && make install

RUN apk add python3-dev
RUN cd depthai-python \
    && cmake -H. -B build -D CMAKE_BUILD_TYPE=Release -D DEPTHAI_ENABLE_BACKWARD=OFF \
    && cmake --build build --parallel $(nproc)

# Package dependencies
RUN mkdir -p /opt/depthai \
    && for dep in $(ldd /depthai-python/build/depthai*.so 2>/dev/null | awk 'BEGIN{ORS=" "}$1 ~/^\//{print $1}$3~/^\//{print $3}' | sed 's/,$/\n/'); do cp "$dep" /opt/depthai; done \
    && mv /depthai-python/build/depthai*.so /opt/depthai

RUN pip3 install -U paho-mqtt paho_socket http_router

FROM base as stage

# ARG TARGETARCH
# ARG S6_OVERLAY_VERSION=3.1.2.1

# RUN apk add --no-cache xz wget
# ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
# RUN tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz
# RUN case ${TARGETARCH} in \
#          "amd64")  S6_ARCH=x86_64  ;; \
#          "arm64")  S6_ARCH=aarch64  ;; \
#     esac \
#     && wget https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${S6_ARCH}.tar.xz -P /tmp
#     && tar -C / -Jxpf /tmp/s6-overlay-${S6_ARCH}.tar.xz
# RUN apk remove xz wget

# Clear Python compiled artifacts
RUN find /usr -depth \
    		\( \
    			\( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
    			-o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \) \
    		\) -exec rm -rf '{}' +

# Clear cache
RUN rm -rf /var/cache && mkdir -p /var/cache

COPY --from=build /opt/depthai /lib
COPY --from=build /usr/lib/python3.10 /usr/lib/python3.10

FROM origin

# Squash the image to save on space
COPY --from=stage / /

ADD docker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Add as separate layer, since it changes often
ADD src/robothub_sdk /lib/robothub_sdk

RUN echo "print('App not installed')" > /run.py

ENTRYPOINT ["docker-entrypoint.sh"]

CMD ["python3", "/run.py"]
