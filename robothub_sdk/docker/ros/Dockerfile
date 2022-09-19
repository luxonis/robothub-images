# syntax=docker/dockerfile:experimental
ARG ROS_VERSION_TAG=galactic-ros-base-focal

FROM ros:${ROS_VERSION_TAG} as base

# Python will buffer output in case of non interactive terminals and we don't want that, because it delays logs
ENV PYTHONPATH=/lib \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ARG TARGETARCH
ARG DEPTHAI_VERSION

# setup timezone
RUN echo 'Etc/UTC' > /etc/timezone && \
    ln -s /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    apt-get update && \
    apt-get install -q -y --no-install-recommends tzdata python3 python3-pip python3-numpy ca-certificates && \
    rm -rf /var/lib/apt/lists/*

FROM base as build

RUN apt-get update && apt-get install -q -y --no-install-recommends wget build-essential cmake pkg-config git
RUN wget https://github.com/libusb/libusb/releases/download/v1.0.25/libusb-1.0.25.tar.bz2 -O libusb.tar.bz2
RUN git clone --depth=1 --recurse-submodules --branch "${DEPTHAI_VERSION}" https://github.com/luxonis/depthai-python.git

RUN tar xf libusb.tar.bz2 \
    && cd libusb-* \
    && ./configure --disable-udev \
    && make -j$(nproc) \
    && make install

RUN apt-get install -q -y --no-install-recommends python3-dev
RUN cd depthai-python \
    && cmake -H. -B build -D CMAKE_BUILD_TYPE=Release -D DEPTHAI_ENABLE_BACKWARD=OFF \
    && cmake --build build --parallel $(nproc)

# Package dependencies
RUN mkdir -p /opt/depthai \
    && for dep in $(ldd /depthai-python/build/depthai*.so 2>/dev/null | awk 'BEGIN{ORS=" "}$1 ~/^\//{print $1}$3~/^\//{print $3}' | sed 's/,$/\n/'); do cp "$dep" /opt/depthai; done \
    && mv /depthai-python/build/depthai*.so /opt/depthai

RUN pip3 install -U paho-mqtt paho_socket http_router

FROM base as stage

COPY --from=build /opt/depthai /lib
COPY --from=build /usr/local/lib/python3.10 /usr/local/lib/python3.10

# Clear Python compiled artifacts
RUN find /usr -depth \
    		\( \
    			\( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
    			-o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \) \
    		\) -exec rm -rf '{}' +

# Clear cache
RUN rm -rf /var/cache && mkdir -p /var/cache

FROM base

# Squash the image to save on space
COPY --from=stage / /

# Add as separate layer, since it changes often
ADD src/robothub_sdk /lib/robothub_sdk

RUN echo "print('App not installed')" > /run.py

CMD ["python3", "/run.py"]
