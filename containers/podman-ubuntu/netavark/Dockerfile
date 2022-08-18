FROM rust:1-slim-buster AS builder

RUN apt update && apt-get install -y\
  git\
  gettext-base\
  make

COPY ./netavark/* /build/
RUN chmod +x /build/build.sh && mkdir /packages
WORKDIR /build

ARG NETAVARK_VERSION
ARG AARDVARK_DNS_VERSION
RUN ./build.sh

FROM scratch

WORKDIR /
COPY --from=builder /packages/* /