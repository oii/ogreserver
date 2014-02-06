include:
  - calibre
  - github
  - gunicorn
  - logs
  - mysql
  - nginx
  - pypiserver
  - rabbitmq
  - rethinkdb
  - supervisor
  - virtualenv-base


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

  pypiserver-log-dir:
    file.directory:
      - user: {{ pillar['app_user'] }}
      - group: {{ pillar['app_user'] }}

  pypiserver-supervisor-config:
    file.managed:
      - context:
          port: 8233
          runas: {{ pillar['app_user'] }}


/srv/ogre:
  file.directory:
    - user: {{ pillar['app_user'] }}
    - group: {{ pillar['app_user'] }}
    - makedirs: true

git-clone-app:
  git.latest:
    - name: git@github.com:oii/ogre.git
    - rev: develop
    - target: /srv/ogre
    - runas: {{ pillar['app_user'] }}
    - require:
      - pkg: git
      - file: github.pky
      - file: /srv/ogre

pip-dependencies-extra:
  pkg.latest:
    - names:
      - libmysqlclient-dev
      - libevent-dev

app-virtualenv:
  virtualenv.managed:
    - name: /home/{{ pillar['app_user'] }}/.virtualenvs/{{ pillar['app_name'] }}
    - requirements: /srv/ogre/ogreserver/config/requirements.txt
    - pre_releases: true
    - user: {{ pillar['app_user'] }}
    - require:
      - pip: virtualenv-init-setuptools
      - pkg: pip-dependencies-extra
      - git: git-clone-app

flask-config:
  file.managed:
    - name: /srv/ogre/ogreserver/config/flask.app.conf.py
    - source: salt://ogreserver/flask.app.conf.py
    - template: jinja
    - user: {{ pillar['app_user'] }}
    - group: {{ pillar['app_user'] }}
    - require:
      - git: git-clone-app

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


/etc/supervisor/conf.d/ogreserver.conf:
  file.managed:
    - source: salt://ogreserver/supervisord.conf
    - template: jinja
    - defaults:
        purge: false
        app_user: {{ pillar['app_user'] }}
    - require:
      - user: {{ pillar['app_user'] }}
      - file: flask-config
      - cmd: rabbitmq-server-running
    - require_in:
      - service: supervisor

ogreserver-service:
  supervisord.running:
    - name: "ogreserver:"
    - update: true
    - require:
      - service: supervisor
    - watch:
      - file: /etc/supervisor/conf.d/ogreserver.conf
      - file: /etc/gunicorn.d/{{ pillar['app_name'] }}.conf.py


#/etc/nginx/conf.d/upstream.conf:
#  file.managed:
#    - source: salt://app_server/upstream.conf
#    - require:
#      - pkg: nginx
#
#/etc/nginx/sites-available/app.basketchaser.com.conf:
#  file.managed:
#    - source: salt://app_server/app.basketchaser.com.conf.sls
#    - template: jinja
#    - require:
#      - pkg: nginx
#      - file: /etc/ssl/app.basketchaser.com.combined.crt
#      - file: /etc/ssl/app.basketchaser.com.key
#
#/etc/nginx/sites-enabled/app.basketchaser.com.conf:
#  file.symlink:
#    - target: /etc/nginx/sites-available/app.basketchaser.com.conf
#    - require:
#      - file: /etc/nginx/sites-available/app.basketchaser.com.conf
