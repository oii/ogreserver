#!/bin/bash -eux

SSH_USERNAME=${SSH_USERNAME:-vagrant}
VMWARE_TOOLS_VERSION=${VMWARE_TOOLS_VERSION:-8.1.0}

if [[ $PACKER_BUILDER_TYPE =~ vmware ]]; then
    echo "==> Installing VMware Tools"
    apt-get install -y "linux-headers-$(uname -r)" build-essential perl git unzip

    cd /tmp || exit
    git clone --branch=force-install https://github.com/mafrosis/vmware-tools-patches.git
    cd vmware-tools-patches || exit
    ./download-tools.sh "$VMWARE_TOOLS_VERSION"
    ./untar-and-patch-and-compile.sh
fi
