include:
  - awscli
  - closure-compiler.local
  - compass.supervisor
  - dev-build.tmux
  - logs
  - s3proxy
  - watchdog

extend:
  gunicorn-config:
    file.managed:
      - context:
          gunicorn_host: "0.0.0.0"
          gunicorn_port: {{ pillar['gunicorn_port'] }}
          worker_class: sync
          timeout: 300
          loglevel: debug

  /etc/supervisor/conf.d/ogreserver.conf:
    file.managed:
      - context:
          purge: true
          loglevel: info

  tmux-powerline-theme:
    file.managed:
      - context:
          gunicorn: true
          celeryd: true

  compass-supervisor-config:
    file.managed:
      - context:
          watch_directory: /srv/ogre/ogreserver/static

  rethinkdb-config:
    file.managed:
      - context:
          production: false

  pypiserver-supervisor-config:
    file.managed:
      - context:
          port: 8233
          runas: {{ pillar['app_user'] }}
          overwrite: true

  app-virtualenv:
    virtualenv.managed:
      - require_in:
        - pip: watchdog

  app-log-directory:
    file.directory:
      - require_in:
        - service: supervisor

  ogreserver-supervisor-service:
    supervisord.running:
      - require_in:
        - supervisord: watchdog-service

  awscli-config:
    file.managed:
      - context:
          s3_access_key: {{ pillar['aws_access_key'] }}
          s3_secret_key: {{ pillar['aws_secret_key'] }}

  ogre-init:
    cmd.run:
      - require:
        - supervisord: s3proxy-supervisor-service


# build dedrm and stick it in the pypiserver cache
build-dedrm:
  cmd.run:
    - name: python setup.py sdist
    - cwd: /srv/ogre/dedrm
    - require:
      - git: git-clone-app
  file.rename:
    - name: /var/pypiserver-cache/dedrm-6.0.7.tar.gz
    - source: /srv/ogre/dedrm/dist/dedrm-6.0.7.tar.gz
    - force: true
    - require:
      - file: pypiserver-package-dir
    - watch:
      - cmd: build-dedrm

# make the logs readable by the login user
logs-chown:
  file.directory:
    - name: /var/log/{{ pillar['app_name'] }}
    - recurse:
      - user
      - group
    - user: {{ pillar['login_user'] }}
    - group: {{ pillar['login_user'] }}
    - require:
      - supervisord: ogreserver-supervisor-service

# setup a dev OGRE user
ogre-create-user:
  cmd.run:
    - name: /home/{{ pillar['app_user'] }}/.virtualenvs/{{ pillar['app_name'] }}/bin/python manage.py create_user {{ pillar['ogre_user_name'] }} {{ pillar['ogre_user_pass'] }} {{ pillar['ogre_user_email'] }}
    - unless: /home/{{ pillar['app_user'] }}/.virtualenvs/{{ pillar['app_name'] }}/bin/python manage.py create_user {{ pillar['ogre_user_name'] }} null null --test
    - cwd: /srv/ogre
    - user: {{ pillar['app_user'] }}
    - require:
      - virtualenv: app-virtualenv
      - cmd: ogre-init

# install pytest
pytest-install:
  pip.installed:
    - requirements: /srv/ogre/requirements_test.txt
    - bin_env: /home/vagrant/.virtualenvs/{{ pillar['app_name'] }}
    - user: {{ pillar['app_user'] }}

# install ipdb
ipdb:
  pip.installed:
    - bin_env: /home/vagrant/.virtualenvs/{{ pillar['app_name'] }}
    - user: {{ pillar['app_user'] }}

# Foundation 5 compass plugin
zurb-foundation-gem:
  gem.installed:
    - name: foundation
    - require:
      - pkg: ruby
    - require_in:
      - supervisord: compass-supervisor-service
