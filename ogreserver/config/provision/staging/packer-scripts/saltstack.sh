#!/bin/bash -eux

SALT_VERSION=${SALT_VERSION:-latest}

if [[ -z $(which curl) ]]; then
  apt-get install -y curl
fi

if [[ ${SALT_VERSION:-} == 'latest' ]]; then
  echo "==> Installing latest Salt version"
  curl -L http://bootstrap.saltstack.org | sudo sh
else
  echo "==> Installing Salt version ${SALT_VERSION}"
  curl -L http://bootstrap.saltstack.org | sudo sh -s -- git "${SALT_VERSION}"
fi

echo "==> Installing pygit2 and git"
apt-get install --no-install-recommends -y python-pip python-dev libgit2-21 libgit2-dev build-essential libffi-dev git
pip install -U pip
pip install pygit2==0.21.4
