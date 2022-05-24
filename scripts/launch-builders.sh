#!/bin/bash
set -e

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install --update

sudo apt-get update
sudo apt-get install -y jq

x86Builder=$(aws ec2 run-instances --image-id ${AWS_X86_IMAGE_ID} --count 1 --instance-type c5.4xlarge --key-name docker-builder --instance-market-options '{ "MarketType": "spot" }' | jq -r .Instances[0])
armBuilder$(aws ec2 run-instances --image-id ${AWS_ARM64_IMAGE_ID} --count 1 --instance-type a1.4xlarge --key-name docker-builder --instance-market-options '{ "MarketType": "spot" }' | jq -r .Instances[0])

x86Ip=$(echo $x86Builder | jq -r .PublicDnsName)
armIp=$(echo $armBuilder | jq -r .PublicDnsName)
echo "::set-output name=x86_ip::${x86Ip}"
echo "::set-output name=arm_ip::${armIp}"

x86BuilderId=$(echo $x86Builder | jq -r .InstanceId)
armBuilderId=$(echo $armBuilder | jq -r .InstanceId)
echo "::set-output name=x86_builder_id::${x86BuilderId}"
echo "::set-output name=arm_builder_id::${armBuilderId}"