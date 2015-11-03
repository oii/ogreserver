include:
  - closure-compiler.local
  - compass.supervisor
  - dev-build.tmux
  - logs
  - ogreclient
  - s3cmd
  - s3proxy
  - watchdog

extend:
  # make supervisorctl accessible to normal user
  supervisor-config:
    file.managed:
      - context:
          socket_mode: "0303"

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
      - defaults:
          purge: true
          app_user: {{ pillar['app_user'] }}
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

  ogre-init:
    cmd.run:
      - require:
        - supervisord: s3proxy-supervisor-service

  s3cfg:
    file.managed:
      - context:
          access_key: local-identity
          secret_key: local-credential
          host_base: localhost:8880
          host_bucket: localhost:8880

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
    - name: /home/{{ pillar['app_user'] }}/.virtualenvs/{{ pillar['app_name'] }}/bin/python manage.py create_user {{ pillar['ogre_user_name'] }} {{ pillar['ogre_user_pass'] }} {{ pillar['ogre_user_email'] }} --role=admin --confirmed
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
