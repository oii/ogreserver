#! /bin/bash
set -e

packer build -only=amazon-ebs -var dist_upgrade=true wheezy77.json
