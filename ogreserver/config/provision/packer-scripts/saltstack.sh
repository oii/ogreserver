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

echo '==> Installing git, pip and pygit2'
apt-get install -y git python-pip build-essential cmake python-dev python-cffi libffi-dev libssl-dev

# install libgit2 from source
git clone --branch v0.23.2 git://github.com/libgit2/libgit2.git /opt/libgit2
cd /opt/libgit2 || exit 1
mkdir build && cd build || exit 1
cmake ..
cmake --build .
cmake --build . --target install

# update shared lib cache
ldconfig

# install pygit2
pip install -U pip pygit2==0.23.2

# cleanup
apt-get remove -y libffi-dev libssl-dev
