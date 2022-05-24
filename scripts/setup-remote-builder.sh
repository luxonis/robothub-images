#!/bin/bash

set -Eeuo pipefail

mkdir -p ~/.ssh/
touch ~/.ssh/aws_key
echo "${SSH_KEY}" > ~/.ssh/aws_key
chmod 600 ~/.ssh/aws_key
eval $(ssh-agent) 
ssh-add ~/.ssh/aws_key

docker buildx create \
  --name remotebuilder \
  --node amd64 \
  --platform linux/amd64,linux/386 \
  ssh://ubuntu@${{ steps.launch_instances.outputs.x86_ip }}

docker buildx create \
  --name remotebuilder \
  --append \
  --node arm64 \
  --platform linux/arm64,linux/arm/v7,linux/arm/v6 \
  ssh://ubuntu@${{ steps.launch_instances.outputs.arm_ip }}

docker buildx use remotebuilder