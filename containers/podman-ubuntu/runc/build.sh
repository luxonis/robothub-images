#!/bin/sh

PKG_ROOT="$(pwd)/runc_${RUNC_VERSION}-1"

mkdir -p "${PKG_ROOT}"

git clone https://github.com/opencontainers/runc.git
cd runc
git checkout "v${RUNC_VERSION}"

make BUILDTAGS="seccomp"
make DESTDIR=$PKG_ROOT install
cd ..

mkdir -p "${PKG_ROOT}/DEBIAN"
envsubst < "./control" > "${PKG_ROOT}/DEBIAN/control"

dpkg-deb --build ${PKG_ROOT}

cp *.deb /packages
