#!/bin/bash

set -eux

code-server --config /vscode.config --bind-addr "${CODE_SERVER_BIND_ADDR}" /app