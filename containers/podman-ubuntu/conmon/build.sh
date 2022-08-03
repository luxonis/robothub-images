#!/bin/sh

export PACKAGE_ARCH="$(dpkg --print-architecture)"
PKG_ROOT="$(pwd)/conmon_${CONMON_VERSION}-1"

mkdir -p $PKG_ROOT/usr/local/libexec/podman

git clone https://github.com/containers/conmon.git
cd conmon
git checkout "v${CONMON_VERSION}"
export GOCACHE="$(mktemp -d)"
make DESTDIR=$PKG_ROOT podman

cd ..
mkdir -p "${PKG_ROOT}/DEBIAN"
envsubst < "./control" > "${PKG_ROOT}/DEBIAN/control"
dpkg-deb --build ${PKG_ROOT}

cp -f *.deb /packages
