base:
  '*':
    - common

  'role:ogreserver':
    - match: grain
    - salt-backports
    - ogreserver
  'role:ogreclient':
    - match: grain
    - ogreclient

  'env:dev':
    - match: grain
    - dev-user
    - dev-build
