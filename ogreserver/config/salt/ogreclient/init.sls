include:
  - github
  - virtualenv-base

app-virtualenv:
  virtualenv.managed:
    - name: /home/{{ pillar['app_user'] }}/.virtualenvs/ogreclient
    - requirements: /srv/ogre/ogreclient/config/requirements.txt
    - user: {{ pillar['app_user'] }}
    - require:
      - git: git-clone-app
