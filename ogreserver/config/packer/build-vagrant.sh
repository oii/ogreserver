#! /bin/bash
set -e

VSTATUS=$(vagrant status)

function destroy {
	echo "There is currently a $1 Vagrant build in this directory."
	read -p 'You must destroy this before building a new one. Destroy now? [y/N] ' -n1 -s
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		vagrant destroy -f
	fi
}

if [[ ! -z $(echo "$VSTATUS" | grep 'default.*running') ]]; then
	destroy 'RUNNING'
fi
if [[ ! -z $(echo "$VSTATUS" | grep 'default.*suspended') ]]; then
	destroy 'SUSPENDED'
fi

# delete an existing box
if [[ ! -z $(vagrant box list | grep ogreserver-packer) ]]; then
	vagrant box remove ogreserver-packer
fi

# run packer build
packer build -only=vmware-iso -force -var dist_upgrade=true wheezy77.json

# add new box to vagrant
vagrant box add ogreserver-packer box/ogreserver-packer.box
