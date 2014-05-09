include:
  - app.virtualenv
  - app.supervisor
  - calibre
  - github
  - gunicorn
  - logs
  - mysql
  - pypiserver
  - rabbitmq
  - rethinkdb


extend:
  supervisor:
    pip.installed:
      - require:
        - virtualenv: app-virtualenv
        - git: git-clone-app

  gunicorn-config:
    file.managed:
      - context:
          worker_class: gevent

  app-virtualenv:
    virtualenv.managed:
      - requirements: /srv/ogreserver/ogreserver/config/requirements.txt
      - pre_releases: true
      - require:
        - pkg: pip-dependencies-extra

  app-log-directory:
    file.directory:
      - require_in:
        - service: supervisor

  ogreserver-supervisor-service:
    supervisord.running:
      - watch:
        - file: /etc/supervisor/conf.d/ogreserver.conf
        - file: /etc/gunicorn.d/ogreserver.conf.py
        - cmd: rabbitmq-server-running

  pypiserver-log-dir:
    file.directory:
      - user: {{ pillar['app_user'] }}
      - group: {{ pillar['app_user'] }}

  pypiserver-supervisor-config:
    file.managed:
      - context:
          port: 8233
          runas: {{ pillar['app_user'] }}


pip-dependencies-extra:
  pkg.latest:
    - names:
      - libmysqlclient-dev
      - libevent-dev

flask-config:
  file.managed:
    - name: /srv/ogre/ogreserver/config/flask.app.conf.py
    - source: salt://ogreserver/flask.app.conf.py
    - template: jinja
    - user: {{ pillar['app_user'] }}
    - group: {{ pillar['app_user'] }}
    - require:
      - git: git-clone-app
    - require_in:
      - service: supervisor

ogre-init:
  cmd.run:
    - name: /home/{{ pillar['app_user'] }}/.virtualenvs/{{ pillar['app_name'] }}/bin/python manage.py init_ogre
    - cwd: /srv/ogre
    - unless: /home/{{ pillar['app_user'] }}/.virtualenvs/{{ pillar['app_name'] }}/bin/python manage.py init_ogre --test
    - user: {{ pillar['app_user'] }}
    - require:
      - virtualenv: app-virtualenv
      - file: flask-config
      - mysql_grants: create-mysql-user-perms
      - pip: rethinkdb-python-driver
