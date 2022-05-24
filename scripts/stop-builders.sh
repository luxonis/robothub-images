#!/bin/bash
set -Eeuo pipefail

aws ec2 terminate-instances --instance-ids "${AWS_X86_BUILDER_ID}" "${$AWS_ARM_BUILDER_ID}"