FROM ubuntu:22.04 as origin

# Python will buffer output in case of non interactive terminals and we don't want that, because it delays logs
ENV PYTHONPATH=/lib \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

FROM origin as base

RUN echo 'Etc/UTC' > /etc/timezone && \
    ln -s /usr/share/zoneinfo/Etc/UTC /etc/localtime && \
    apt-get update && \
    apt-get install -q -y --no-install-recommends python3 python3-pip python3-opencv && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

FROM base as build

RUN apt-get update && \
    apt-get install -q -y --no-install-recommends python3-dev git ca-certificates wget bzip2 build-essential cmake && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

RUN wget https://github.com/libusb/libusb/releases/download/v1.0.25/libusb-1.0.25.tar.bz2 -O libusb.tar.bz2 && \
    git clone --depth=1 --recurse-submodules https://github.com/luxonis/depthai-python.git

COPY docker_images/linux_netlink.c /tmp/linux_netlink.c
RUN tar xf libusb.tar.bz2 \
    && cd libusb-* \
    && rm ./libusb/os/linux_netlink.c \
    && cp /tmp/linux_netlink.c ./libusb/os/linux_netlink.c \
    && ./configure --disable-udev \
    && make -j$(nproc) \
    && cp ./libusb/.libs/libusb-1.0.so.0.3.0 /tmp/libusb-1.0.so

RUN cd depthai-python \
    && cmake -H. -B build -D CMAKE_BUILD_TYPE=Release -D DEPTHAI_ENABLE_BACKWARD=OFF \
    && cmake --build build --parallel $(nproc)

# Package dependencies
RUN mkdir -p /opt/depthai \
    && for dep in $(ldd /depthai-python/build/depthai*.so 2>/dev/null | awk 'BEGIN{ORS=" "}$1 ~/^\//{print $1}$3~/^\//{print $3}' | sed 's/,$/\n/'); do cp "$dep" /opt/depthai; done \
    && mv /depthai-python/build/depthai*.so /opt/depthai

# Clear Python compiled artifacts
RUN find /usr -depth \
    		\( \
    			\( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
    			-o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' -o -name 'libpython*.a' \) \) \
    		\) -exec rm -rf '{}' +

RUN git clone --branch "develop" https://github.com/luxonis/depthai depthai_temporary && cp -r depthai_temporary/depthai_sdk/src/depthai_sdk /tmp/depthai_sdk

RUN rm -rf depthai_temporary

RUN git clone --branch "experimental" https://github.com/luxonis/robothub-oak rh_oak_temporary && cp -r rh_oak_temporary/src/robothub_oak /tmp/robothub_oak

RUN rm -rf rh_oak_temporary

RUN pip3 install av PyTurboJPEG==1.6.4 marshmallow==3.17.0 distinctipy xmltodict numpy opencv-contrib-python blobconverter pytube packaging PyYAML boto3 botocore==1.29.98 s3transfer==0.6.0 jmespath==1.0.1 certifi==2020.6.20 idna==3.3 charset-normalizer urllib3==1.26.5 python-dateutil==2.8.1

RUN apt-get purge -y --auto-remove \
    build-essential \
    cmake \
    git \
    wget \
    bzip2 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

FROM base

# Squash the image to save on space
COPY --from=build /tmp/depthai_sdk /lib/depthai_sdk
COPY --from=build /tmp/robothub_oak /lib/robothub_oak
COPY --from=build /opt/depthai /lib
COPY --from=build /tmp/libusb-1.0.so /lib/libusb-1.0.so
COPY --from=build /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages

RUN echo "print('App not installed')" > /run.py

CMD ["python3", "/run.py"]
