#!/usr/bin/sh

pip3 install --no-deps --no-cache-dir --extra-index-url https://artifacts.luxonis.com/artifactory/luxonis-python-snapshot-local/ depthai==${DEPTHAI_VERSION}
pip3 install --no-deps --no-cache-dir git+https://github.com/luxonis/depthai.git@${DEPTHAI_SDK_VERSION}#subdirectory=depthai_sdk
pip3 install --no-deps --no-cache-dir robothub-oak
