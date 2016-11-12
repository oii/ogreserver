include:
  - app.source
  - app.supervisor
  - calibre
  - closure-compiler
  - gunicorn
  - libsass
  - mysql
  - nodejs
  - redis
  - rethinkdb


extend:
  gunicorn-config:
    file.managed:
      - context:
          worker_class: gevent
          gunicorn_port: {{ pillar['gunicorn_port'] }}

  app-virtualenv:
    virtualenv.managed:
      - requirements: /srv/{{ pillar['app_directory_name'] }}/ogreserver/config/requirements.txt
      - require:
        - pkg: pip-dependencies-extra
        - git: git-clone-app

  /etc/supervisor/conf.d/ogreserver.conf:
    file.managed:
      - context:
          app_dir: {{ pillar['app_directory_name'] }}
          workers:
            high: 0
            normal: 0
            low: 1

  ogreserver-supervisor-service:
    supervisord.running:
      - require:
        - service: redis
        - virtualenv: app-virtualenv
      - watch:
        - file: /etc/supervisor/conf.d/{{ pillar['app_name'] }}.conf
        - file: /etc/gunicorn.d/{{ pillar['app_name'] }}.conf.py


venv-dependencies:
  pkg.latest:
    - names:
      - python-dev
      - python-pip
      - build-essential
    - require:
      - pkg: required-packages

virtualenv:
  pip.installed:
    - require:
      - pkg: venv-dependencies

app-virtualenv:
  virtualenv.managed:
    - name: /srv/{{ pillar['app_directory_name'] }}
    - requirements: /srv/{{ pillar['app_directory_name'] }}/ogreserver/config/requirements.txt
    - user: {{ pillar['app_user'] }}
    - require:
      - pip: virtualenv
      - user: {{ pillar['app_user'] }}

# celerybeat schedule directory
/var/celerybeat:
  file.directory:
    - user: {{ pillar['app_user'] }}
    - group: {{ pillar['app_user'] }}
    - require_in:
      - service: supervisor

# storage for whoosh DB
/var/ogre:
  file.directory:
    - user: {{ pillar['app_user'] }}
    - group: {{ pillar['app_user'] }}

# install bower.io for Foundation 5
bower:
  npm.installed:
    - require:
      - pkg: nodejs

bower-ogreserver-install:
  cmd.run:
    - name: bower install --config.interactive=false
    - cwd: /srv/{{ pillar['app_directory_name'] }}/ogreserver/static
    - user: {{ pillar['app_user'] }}
    - unless: test -d /srv/{{ pillar['app_directory_name'] }}/ogreserver/static/bower_components
    - require:
      - git: git-clone-app


/srv/{{ pillar['app_directory_name'] }}/ogreserver/static/stylesheets:
  file.directory:
    - user: {{ pillar['app_user'] }}
    - group: {{ pillar['app_user'] }}
    - require:
      - git: git-clone-app

# compile JS and SASS
static-asset-compile:
  cmd.run:
    - name: make dev
    - cwd: /srv/{{ pillar['app_directory_name'] }}/ogreserver/static
    - user: {{ pillar['app_user'] }}
    - require:
      - cmd: bower-ogreserver-install


pip-dependencies-extra:
  pkg.latest:
    - names:
      - libmysqlclient-dev
      - libevent-dev

flask-config-dir:
  file.directory:
    - name: /etc/ogre
    - user: {{ pillar['app_user'] }}
    - group: {{ pillar['app_user'] }}

flask-config:
  file.managed:
    - name: /etc/ogre/flask.app.conf.py
    - source: salt://ogreserver/flask.app.conf.py
    - template: jinja
    - user: {{ pillar['app_user'] }}
    - group: {{ pillar['app_user'] }}
    - require:
      - file: flask-config-dir
    - require_in:
      - service: supervisor

ogre-init:
  cmd.run:
    - name: bin/python manage.py init_ogre
    - cwd: /srv/{{ pillar['app_directory_name'] }}
    - unless: bin/python manage.py init_ogre --test
    - user: {{ pillar['app_user'] }}
    - require:
      - virtualenv: app-virtualenv
      - file: flask-config
      - mysql_grants: create-mysql-user-perms
      - pip: rethinkdb-python-driver
