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

  create-ogre-user:
    cmd.run:
      - require:
        - virtualenv: app-virtualenv
        - cmd: ogre-init

  create-ogrebot-user:
    cmd.run:
      - require:
        - virtualenv: app-virtualenv
        - cmd: ogre-init

  create-postgres-user:
    postgres_user.present:
      - createdb: true
      - superuser: true


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
    - bin_env: /var/cache/ogre/venv
    - user: {{ pillar['app_user'] }}
    - require:
      - virtualenv: app-virtualenv
