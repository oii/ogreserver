base:
  '*':
    - common
    - ogreserver
    - disable-salt-minion

  'G@env:prod or G@env:staging':
    - match: compound
    - nginx.config
    - ogreserver.prod

  'env:dev':
    - match: grain
    - dev-user
    - dev-build
