#!/bin/bash -eux

GIT_REVISION=${GIT_REVISION:-master}
DEBUG=${DEBUG:-false}

mkdir /etc/ogre
cd /etc/ogre || exit 2

echo 'Created /etc/ogre'
echo "Retrieving prod_vars.sesame from oii/ogreserver at ${GIT_REVISION}"

curl --silent -o /tmp/sesame.sh https://raw.githubusercontent.com/mafrosis/sesame.sh/master/sesame.sh &>/dev/null
chmod +x /tmp/sesame.sh

# fetch default_vars
curl --silent -o /etc/ogre/default_vars.sls "https://raw.githubusercontent.com/oii/ogreserver/${GIT_REVISION}/config/pillar/default_vars.sls"

if [[ $DEBUG == true ]]; then
	echo "https://raw.githubusercontent.com/oii/ogreserver/${GIT_REVISION}/config/pillar/default_vars.sls"
	cat /etc/ogre/default_vars.sls
fi

# fetch encrypted prod_vars
curl --silent -o /tmp/prod_vars.sesame "https://raw.githubusercontent.com/oii/ogreserver/${GIT_REVISION}/config/pillar/prod_vars.sesame"

if [[ $DEBUG == true ]]; then
	echo "https://raw.githubusercontent.com/oii/ogreserver/${GIT_REVISION}/config/pillar/prod_vars.sesame"
	cat /tmp/prod_vars.sesame
fi

if [[ $? -gt 0 ]]; then
	echo 'Encrypted pillar not found on Github'
	exit 1
fi

/tmp/sesame.sh d -p "${SESAME_PASSWORD}" /tmp/prod_vars.sesame

# make pillar readable by salt
chown -R root:root /etc/ogre/*
chmod 640 /etc/ogre/*

if [[ -f /etc/ogre/prod_vars.sls ]]; then
	echo 'Decrypted prod_vars pillar into /etc/ogre'

else
	# we have fail
	exit 44
fi
