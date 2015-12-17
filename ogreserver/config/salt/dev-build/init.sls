include:
  - closure-compiler.local
  - create-ogre-user
  - dev-build.tmux
  - github
  - libsass
  - logs
  - ogreclient
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

  sassc-install:
    cmd.run:
      - require_in:
        - supervisord: watchdog-service

  static-asset-compile:
    cmd.run:
      - require:
        - cmd: closure-compiler

  ogre-init:
    cmd.run:
      - require:
        - supervisord: s3proxy-supervisor-service

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

# install pytest
pytest-install:
  pip.installed:
    - requirements: /srv/ogre/requirements_test.txt
    - bin_env: /home/vagrant/.virtualenvs/{{ pillar['app_name'] }}
    - user: {{ pillar['app_user'] }}
    - require:
      - virtualenv: app-virtualenv

# install ipdb
ipdb:
  pip.installed:
    - bin_env: /home/vagrant/.virtualenvs/{{ pillar['app_name'] }}
    - user: {{ pillar['app_user'] }}
