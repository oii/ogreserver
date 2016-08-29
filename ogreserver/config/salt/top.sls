base:
  '*':
    - common
    - ogreserver

  'G@env:prod or G@env:staging':
    - match: compound
    - nginx.config
    - ogreserver.prod

  'env:staging':
    - match: grain
    - create-ogre-user

  'env:dev':
    - match: grain
    - dev-user
    - dev-build
