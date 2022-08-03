#!/bin/sh

PKG_ROOT="$(pwd)/podman_${PODMAN_VERSION}-1"

mkdir -p "${PKG_ROOT}/usr/local/bin"

git clone https://github.com/containers/podman/
cd podman
git checkout "v${PODMAN_VERSION}"
make BUILDTAGS="seccomp apparmor systemd"
make DESTDIR=$PKG_ROOT install
cd ..

mkdir -p "${PKG_ROOT}/etc/containers"
curl -L -o "${PKG_ROOT}/etc/containers/registries.conf" https://src.fedoraproject.org/rpms/containers-common/raw/main/f/registries.conf
curl -L -o "${PKG_ROOT}/etc/containers/policy.json" https://src.fedoraproject.org/rpms/containers-common/raw/main/f/default-policy.json

mkdir -p "${PKG_ROOT}/DEBIAN"
envsubst < "./control" > "${PKG_ROOT}/DEBIAN/control"

dpkg-deb --build ${PKG_ROOT}
cp -f *.deb /packages
