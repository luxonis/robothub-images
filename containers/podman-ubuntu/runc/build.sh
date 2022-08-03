#!/bin/sh

set -eux

export PACKAGE_ARCH="$(dpkg --print-architecture)"

PKG_ROOT="$(pwd)/runc_${RUNC_VERSION}-1"

mkdir -p "${PKG_ROOT}"

git clone --depth 1 --branch "v${RUNC_VERSION}" https://github.com/opencontainers/runc.git
cd runc

make BUILDTAGS="seccomp"
make DESTDIR=$PKG_ROOT install
cd ..

mkdir -p "${PKG_ROOT}/DEBIAN"
envsubst < "./control" > "${PKG_ROOT}/DEBIAN/control"

dpkg-deb --build ${PKG_ROOT}

cp *.deb /packages
