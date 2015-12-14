base:
  'role:ogreserver':
    - match: grain
    - ogreserver

  'env:dev':
    - match: grain
    - dev_vars
  'G@env:prod or G@env:staging':
    - match: compound
    - prod_vars
