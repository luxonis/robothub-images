#!/bin/bash

pip3 install --no-deps --no-cache-dir git+https://github.com/luxonis/depthai.git@${DEPTHAI_SDK_VERSION}#subdirectory=depthai_sdk
pip3 install --no-deps --no-cache-dir robothub-oak==${ROBOTHUB_OAK_VERSION}
