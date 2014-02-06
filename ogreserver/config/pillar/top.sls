base:
  'role:ogreserver':
    - match: grain
    - ogreserver
  'role:ogreclient':
    - match: grain
    - ogreclient

  'env:dev':
    - match: grain
    - dev_vars
  'env:prod':
    - match: grain
    - prod_vars

  '*':
    - github_pky
