include:
  - closure-compiler
  - create-ogre-user
  - dev-build.tmux
  - github
  - libsass
  - logs
  - ogreclient
  - s3proxy


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

  app-log-directory:
    file.directory:
      - require_in:
        - service: supervisor

  static-asset-compile:
    cmd.run:
      - require:
        - file: closure-compiler-service

  ogre-init:
    cmd.run:
      - require:
        - supervisord: s3proxy-supervisor-service

  ogre-create-user:
    cmd.run:
      - require:
        - virtualenv: app-virtualenv
        - cmd: ogre-init

  create-postgres-user:
    postgres_user.present:
      - createdb: true


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

# install extra dev reqs
requirements-dev-install:
  pip.installed:
    - requirements: /srv/ogre/ogreserver/config/requirements-dev.txt
    - bin_env: /srv/{{ pillar['app_directory_name'] }}
    - user: {{ pillar['app_user'] }}
    - require:
      - virtualenv: app-virtualenv
