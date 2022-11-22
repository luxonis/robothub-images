#!/bin/sh

set -eux

ARCH="$(uname -m)"
export PACKAGE_ARCH="$(dpkg --print-architecture)"
PKG_ROOT="$(pwd)/conmon_${CONMON_VERSION}"

mkdir -p $PKG_ROOT/usr/local/libexec/podman

git clone --depth 1 --branch "v${CONMON_VERSION}" https://github.com/containers/conmon.git
cd conmon
export GOCACHE="$(mktemp -d)"
make DESTDIR=$PKG_ROOT podman

cd ..
mkdir -p "${PKG_ROOT}/DEBIAN"
envsubst < "./control" > "${PKG_ROOT}/DEBIAN/control"

#dpkg-deb --build ${PKG_ROOT}
#cp -f *.deb /packages

tar -zcvf /packages/conmon_${CONMON_VERSION}_${ARCH}.tar.gz -C "${PKG_ROOT}" usr
