include:
  - create-app-user
  - hostname.cloud-init
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
        - service: redis
        - file: newrelic-config

  create-app-user:
    user.present:
      - require_in:
        - file: app-directory

  # disable ogreserver.conf so nginx will start before SSL certs are ready
  # SSL certs are created at EC2 instance start
  /etc/nginx/sites-enabled/ogreserver.conf:
    file.symlink:
      - name: /tmp/unused.conf

gevent:
  pip.installed:
    - bin_env: /var/cache/ogre/venv
    - user: {{ pillar['app_user'] }}
    - require:
      - virtualenv: app-virtualenv
    - require_in:
      - service: supervisor

# install extra production reqs
requirements-prod-install:
  pip.installed:
    - requirements: /srv/ogre/ogreserver/config/requirements-prod.txt
    - bin_env: /var/cache/ogre/venv
    - user: {{ pillar['app_user'] }}
    - require:
      - virtualenv: app-virtualenv
    - require_in:
      - cmd: ogre-init

# symlink files so they're available statically via nginx
/srv/ogre/ogreserver/robots.txt:
  file.symlink:
    - target: /srv/ogre/ogreserver/static/robots.txt

/srv/ogre/ogreserver/install:
  file.symlink:
    - target: /srv/ogre/script/install
