#!/bin/bash -eux

SALT_VERSION=${SALT_VERSION:-latest}

if [[ -z $(which curl) ]]; then
  apt-get install -y curl
fi

if [[ ${SALT_VERSION:-} == 'latest' ]]; then
  echo "==> Installing latest Salt version"
  curl -L http://bootstrap.saltstack.org | bash -P | grep -v copying | grep -v byte-compiling
else
  echo "==> Installing Salt version ${SALT_VERSION}"
  curl -L http://bootstrap.saltstack.org | bash -s -- -P git "${SALT_VERSION}" | grep -v copying | grep -v byte-compiling
fi

echo '==> Installing git and pip'
apt-get install -y git python-pip python-dev

# update pip
pip install -U pip
