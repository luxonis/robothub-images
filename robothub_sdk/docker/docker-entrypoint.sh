#!/bin/sh

echo "Running docker-entrypoint $*"

if [ -d /public ]; then
  # sync static assets to server root directory
  echo "Copying static assets"
  mkdir -p /storage/public
  cp -r /public/* /storage/public
fi

exec "$@"
