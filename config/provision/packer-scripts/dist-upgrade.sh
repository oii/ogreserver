#!/bin/bash -eux

echo "==> Performing dist-upgrade (all packages and kernel)"
apt-get -y update
DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade --force-yes
