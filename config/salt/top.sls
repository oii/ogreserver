base:
  '*':
    - common
    - ogreserver
    - disable-salt-minion

  'G@env:prod or G@env:staging':
    - match: compound
    - ogreserver.prod
    - datadog

  'env:dev':
    - match: grain
    - dev-user
    - dev-build
