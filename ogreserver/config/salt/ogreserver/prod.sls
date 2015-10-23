include:
  - ogreserver
  - newrelic
  - nginx.acme-ssl


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
    - bin_env: /home/{{ pillar['app_user'] }}/.virtualenvs/{{ pillar['app_name'] }}
    - user: {{ pillar['app_user'] }}
    - require_in:
      - service: supervisor

# build ogreclient and stick it in the pypiserver cache
build-ogreclient:
  cmd.run:
    - name: python setup.py sdist
    - cwd: /srv/ogre/ogreclient
  file.rename:
    - name: /var/pypiserver-cache/ogreclient-{{ pillar['ogreclient_version'] }}.tar.gz
    - source: /srv/ogre/ogreclient/dist/ogreclient-{{ pillar['ogreclient_version'] }}.tar.gz
    - force: true
    - require:
      - file: pypiserver-package-dir
    - watch:
      - cmd: build-ogreclient

# symlink files so they're available statically via nginx
/srv/ogre/ogreserver/robots.txt:
  file.symlink:
    - target: /srv/ogre/ogreserver/static/robots.txt

/srv/ogre/ogreserver/install:
  file.symlink:
    - target: /srv/ogre/bin/install
