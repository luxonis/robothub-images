#!/bin/bash
set -Eeuo pipefail

mkdir -p ~/.ssh/
touch ~/.ssh/aws_key
echo "${SSH_KEY}" >~/.ssh/aws_key
chmod 600 ~/.ssh/aws_key
eval $(ssh-agent)
ssh-add ~/.ssh/aws_key

touch ~/.ssh/config
echo "Host ${X86_BUILDER_IP}" >>~/.ssh/config
echo "  HostName ${X86_BUILDER_IP}" >>~/.ssh/config
echo "  User ubuntu" >>~/.ssh/config
echo "  StrictHostKeyChecking no" >>~/.ssh/config
echo "  IdentityFile /home/runner/.ssh/aws_key" >>~/.ssh/config
echo "Host ${ARM_BUILDER_IP}" >>~/.ssh/config
echo "  HostName ${ARM_BUILDER_IP}" >>~/.ssh/config
echo "  User ubuntu" >>~/.ssh/config
echo "  StrictHostKeyChecking no" >>~/.ssh/config
echo "  IdentityFile /home/runner/.ssh/aws_key" >>~/.ssh/config

echo "configuring X86 builder at ${X86_BUILDER_IP}"
docker buildx create \
  --name remotebuilder \
  --node amd64 \
  --platform linux/amd64,linux/386 \
  --driver=docker-container \
  "ssh://ubuntu@${X86_BUILDER_IP}"

echo "configuring ARM builder at ${ARM_BUILDER_IP}"
docker buildx create \
  --name remotebuilder \
  --append \
  --node arm64 \
  --platform linux/arm64,linux/arm/v7,linux/arm/v6 \
  --driver=docker-container \
  "ssh://ubuntu@${ARM_BUILDER_IP}"

docker buildx inspect --bootstrap --builder remotebuilder
