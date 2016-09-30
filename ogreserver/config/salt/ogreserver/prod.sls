include:
  - create-app-user
  - hostname
  - mysql.prod
  - newrelic
  - nginx.acme-ssl
  - ogreserver


extend:
  nginx:
    service.running:
      - watch:
        - file: /etc/nginx/conf.d/http.conf
        - file: /etc/nginx/proxy_params
        - file: /etc/nginx/sites-enabled/{{ pillar['app_name'] }}.conf

  {% for port in [80, 443] %}
  nginx-app-config-{{ port }}:
    file.managed:
      - context:
          server_name: {{ pillar['dns'][grains['env']] }}
          root: /srv/ogre/ogreserver
          upstream_gzip: true
          static_dir: /static/
          static_alias: /srv/ogre/ogreserver/static/dist/
  {% endfor %}

  static-asset-compile:
    cmd.run:
      - name: make prod

  ogreserver-supervisor-service:
    supervisord.running:
      - require:
        - cmd: rabbitmq-server-running
        - file: newrelic-config


gevent:
  pip.installed:
    - bin_env: /home/{{ pillar['app_user'] }}/.virtualenvs/{{ pillar['virtualenv_name'] }}
    - user: {{ pillar['app_user'] }}
    - require_in:
      - service: supervisor

awscli:
  pip.installed

# build ogreclient and extra client tooling
build-ogreclient:
  cmd.run:
    - name: make release
    - cwd: /srv/ogre/ogreclient
    - require:
      - pip: awscli
    - env:
      - AWS_ACCESS_KEY_ID: {{ pillar['aws_access_key'] }}
      - AWS_SECRET_ACCESS_KEY: {{ pillar['aws_secret_key'] }}
      - AWS_DEFAULT_REGION: {{ pillar['aws_region'] }}
      - ENV: {{ grains['env'] }}

# symlink files so they're available statically via nginx
/srv/ogre/ogreserver/robots.txt:
  file.symlink:
    - target: /srv/ogre/ogreserver/static/robots.txt

/srv/ogre/ogreserver/install:
  file.symlink:
    - target: /srv/ogre/bin/install
