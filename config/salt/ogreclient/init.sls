include:
  - virtualenv

ogreclient-virtualenv:
  virtualenv.managed:
    - name: /home/{{ pillar['app_user'] }}/.virtualenvs/ogreclient
    - user: {{ pillar['app_user'] }}

ogreclient-install:
  cmd.run:
    - name: /home/{{ pillar['app_user'] }}/.virtualenvs/ogreclient/bin/pip install -e .
    - cwd: /srv/ogre/ogreclient
    - user: {{ pillar['app_user'] }}
