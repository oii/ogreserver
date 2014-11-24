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

  'G@role:ogreserver and G@env:prod':
    - match: compound
    - nginx.config
    - ogreserver.prod

  'env:dev':
    - match: grain
    - dev-user
    - dev-build
