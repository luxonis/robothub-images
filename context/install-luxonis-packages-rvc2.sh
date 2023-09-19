#!/usr/bin/sh

pip3 install --no-deps --no-cache-dir --extra-index-url https://artifacts.luxonis.com/artifactory/luxonis-python-release-local/ depthai==${DEPTHAI_VERSION}
pip3 install --no-deps --no-cache-dir depthai-sdk==${DEPTHAI_SDK_VERSION}
pip3 install --no-deps --no-cache-dir robothub-oak==${ROBOTHUB_OAK_VERSION}
