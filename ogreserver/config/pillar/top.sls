base:
  'role:ogreserver':
    - match: grain
    - ogreserver

  'env:dev':
    - match: grain
    - dev_vars
  'env:prod':
    - match: grain
    - prod_vars

  '*':
    - github_pky
