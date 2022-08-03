ARG GO_LANG_VERSION
FROM golang:${GO_LANG_VERSION}

RUN apt update && apt-get install -y \
  gettext-base\
  git \
  libseccomp-dev \
  dpkg-dev && rm -rf /var/lib/apt/lists/* \
  && mkdir /build
COPY ./runc/* /build/
RUN chmod +x /build/build.sh && mkdir /packages
WORKDIR /build

ARG RUNC_VERSION
RUN ./build.sh

FROM scratch

WORKDIR /
COPY --from=builder /packages/* /