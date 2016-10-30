#! /bin/bash

USAGE='Usage: setup-drm-tests.sh'

# copy script to /tmp on host machine
cp 'bin/setup-drm-test-kindle-osx.sh' /tmp/host_machine
chmod +x '/tmp/host_machine/setup-drm-test-kindle-osx.sh'

echo "DRM'd books will come from Kindle for Mac, installed on the host OS."
echo "A script has been copied into the host machine's /tmp/setup-drm-test-kindle-osx.sh"
echo ''
read -p 'Run that script now, and press enter to continue..' -n1 -s

if [[ ! -f /tmp/host_machine/DRM.azw ]]; then
	echo 'An error appears to have occurred in host machine script:'
	echo '  DRM.azw not found in /tmp/host_machine'
	exit 1
fi

# copy file from host OS into test directory
cp /tmp/host_machine/DRM.azw tests/ebooks

echo ''
echo 'Done. DRM.azw copied into tests/ebooks'
