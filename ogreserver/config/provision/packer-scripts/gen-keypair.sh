#!/bin/bash -eux

ssh-keygen -t rsa -N '' -f /tmp/tmp.key

cat /tmp/tmp.key
cat /tmp/tmp.key.pub >> /home/admin/.ssh/authorized_keys
