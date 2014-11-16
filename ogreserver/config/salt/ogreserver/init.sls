include:
  - app.virtualenv
  - app.supervisor
  - calibre
  - compass
  - github
  - gunicorn
  - mysql
  - nodejs
  - pypiserver
  - rabbitmq
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
      - pre_releases: true
      - require:
        - pkg: pip-dependencies-extra

  ogreserver-supervisor-service:
    supervisord.running:
      - require:
        - cmd: rabbitmq-server-running
      - watch:
        - file: /etc/supervisor/conf.d/{{ pillar['app_name'] }}.conf
        - file: /etc/gunicorn.d/{{ pillar['app_name'] }}.conf.py

  pypiserver-log-dir:
    file.directory:
      - user: {{ pillar['app_user'] }}
      - group: {{ pillar['app_user'] }}

  pypiserver-supervisor-config:
    file.managed:
      - context:
          port: 8233
          runas: {{ pillar['app_user'] }}

  {% if grains.get('env', '') == 'prod' %}
  nginx:
    service.running:
      - watch:
        - file: /etc/nginx/conf.d/http.conf
        - file: /etc/nginx/proxy_params
        - file: /etc/nginx/sites-enabled/{{ pillar['app_name'] }}.conf

  /etc/nginx/sites-available/{{ pillar['app_name'] }}.conf:
    file.managed:
      - context:
          server_name: ogre.oii.yt
          root: /srv/{{ pillar['app_directory_name'] }}
  {% endif %}


# install bower.io for Foundation 5
bower:
  npm.installed:
    - require:
      - cmd: npm-install

bower-ogreserver-install:
  cmd.run:
    - name: bower install --config.interactive=false
    - cwd: /srv/{{ pillar['app_directory_name'] }}/ogreserver/static
    - user: {{ pillar['app_user'] }}
    - unless: test -d /srv/{{ pillar['app_directory_name'] }}/ogreserver/static/bower_components
    - require:
      - git: git-clone-app

# compile sass to css
sass-compile:
  cmd.run:
    - name: compass compile --force --boring
    - cwd: /srv/{{ pillar['app_directory_name'] }}/ogreserver/static
    - user: {{ pillar['app_user'] }}
    - require:
      - git: git-clone-app
      - gem: compass-gem
      - cmd: bower-ogreserver-install


{% if grains.get('env', '') == 'prod' %}
gevent:
  pip.installed:
    - bin_env: /home/{{ pillar['app_user'] }}/.virtualenvs/{{ pillar['app_name'] }}
    - user: {{ pillar['app_user'] }}
    - require_in:
      - service: supervisor
{% endif %}

pip-dependencies-extra:
  pkg.latest:
    - names:
      - libmysqlclient-dev
      - libevent-dev

flask-config:
  file.managed:
    - name: /srv/{{ pillar['app_directory_name'] }}/flask.app.conf.py
    - source: salt://ogreserver/flask.app.conf.py
    - template: jinja
    - user: {{ pillar['app_user'] }}
    - group: {{ pillar['app_user'] }}
    - require:
      - git: git-clone-app
    - require_in:
      - service: supervisor

ogre-init:
  cmd.run:
    - name: /home/{{ pillar['app_user'] }}/.virtualenvs/{{ pillar['app_name'] }}/bin/python manage.py init_ogre
    - cwd: /srv/ogre
    - unless: /home/{{ pillar['app_user'] }}/.virtualenvs/{{ pillar['app_name'] }}/bin/python manage.py init_ogre --test
    - user: {{ pillar['app_user'] }}
    - require:
      - virtualenv: app-virtualenv
      - file: flask-config
      - mysql_grants: create-mysql-user-perms
      - pip: rethinkdb-python-driver
