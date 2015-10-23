#!/bin/bash -eux

echo "==> Performing dist-upgrade (all packages and kernel)"
DEBIAN_FRONTEND=noninteractive apt-get -y dist-upgrade --force-yes
