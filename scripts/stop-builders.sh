#!/bin/bash
set -Eeuo pipefail

aws terminate --instance-id $AWS_X86_BUILDER_ID
aws terminate --instance-id $AWS_ARM_BUILDER_ID