base:
  '*':
    - common

  'role:ogreserver':
    - match: grain
    - salt-backports
    - ogreserver

  'G@role:ogreserver and G@env:prod':
    - match: compound
    - nginx.config
    - ogreserver.prod

  'env:dev':
    - match: grain
    - dev-user
    - dev-build
