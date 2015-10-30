#!/bin/bash -eux

mkdir /etc/ogreserver
cd /etc/ogreserver || exit

curl -o /tmp/sesame.sh https://raw.githubusercontent.com/mafrosis/sesame.sh/master/sesame.sh &>/dev/null
chmod +x /tmp/sesame.sh

curl -L -o /tmp/prod_vars.sesame https://raw.githubusercontent.com/oii/ogre/apis/ogreserver/config/pillar/prod_vars.sesame &>/dev/null

/tmp/sesame.sh d -p "${SESAME_PASSWORD}" /tmp/prod_vars.sesame

echo 'Decrypted prod_vars pillar into /etc/ogreserver'

ls -l /etc | grep ogreserver
ls -l /etc/ogreserver
head /etc/ogreserver/prod_vars.sls

#sleep 600

#tee /tmp/ogreserver/top.sls > /dev/null <<EOF
#base:
#  '*':
#    - prod_vars
#EOF
