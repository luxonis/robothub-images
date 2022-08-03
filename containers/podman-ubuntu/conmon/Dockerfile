ARG GO_LANG_VERSION
FROM golang:${GO_LANG_VERSION}

RUN apt update && apt-get install -y \
  gettext-base\
  gcc \
  git \
  libc6-dev \
  libglib2.0-dev \
  libseccomp-dev \
  libsystemd-dev \
  pkg-config \
  make \
  runc \
  dpkg-dev && rm -rf /var/lib/apt/lists/* \
  && mkdir /build
COPY ./conmon/* /build/
RUN chmod +x /build/build.sh && mkdir /packages
WORKDIR /build

RUN ./build.sh
