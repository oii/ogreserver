include:
  - create-app-user
  - hostname.cloud-init
  - mysql.prod
  - nginx.acme-ssl
  - ogreserver


extend:
  {% for port in [80, 443] %}
  nginx-app-config-{{ port }}:
    file.managed:
      - context:
          server_name: {{ pillar['dns'][grains['env']] }}
          root: /srv/ogre
          upstream_gzip: true
          static_dir: /static/
          static_alias: /srv/ogre/static/dist/
          stub_status: true
  {% endfor %}

  static-asset-compile:
    cmd.run:
      - name: make prod

  ogreserver-supervisor-service:
    supervisord.running:
      - require:
        - service: redis

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
    - requirements: /srv/ogre/config/requirements-prod.txt
    - bin_env: /var/cache/ogre/venv
    - user: {{ pillar['app_user'] }}
    - require:
      - virtualenv: app-virtualenv
    - require_in:
      - cmd: ogre-init

# symlink files so they're available statically via nginx
/srv/ogre/robots.txt:
  file.symlink:
    - target: /srv/ogre/static/robots.txt

/srv/ogre/install:
  file.symlink:
    - target: /srv/ogre/script/install
