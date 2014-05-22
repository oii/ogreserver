include:
  - compass
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

  tmux-powerline-theme:
    file.managed:
      - context:
          gunicorn: true
          celeryd: true

  compass-supervisor-config:
    file.managed:
      - context:
          watch_directory: /srv/ogreserver/ogreserver/static

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

  ogreserver-supervisor-service:
    supervisord.running:
      - require_in:
        - supervisord: watchdog-service


# build dedrm and stick it in the pypiserver cache
build-dedrm:
  cmd.run:
    - name: python setup.py sdist
    - cwd: /srv/ogreserver/dedrm
    - require:
      - git: git-clone-app
  file.rename:
    - name: /var/pypiserver-cache/dedrm-6.0.7.tar.gz
    - source: /srv/ogreserver/dedrm/dist/dedrm-6.0.7.tar.gz
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
    - cwd: /srv/ogreserver
    - user: {{ pillar['app_user'] }}
    - require:
      - virtualenv: app-virtualenv
      - cmd: ogre-init

# ruby plumbing for Zurb Sass framework
zurb-rubygems:
  pkg.installed:
    - name: rubygems

zurb-foundation-gem:
  gem.installed:
    - name: zurb-foundation
    - require:
      - pkg: zurb-rubygems
    - require_in:
      - supervisord: compass-supervisor-service

# install tmux segments for gunicorn & celeryd state
{% for app in ('gunicorn', 'celeryd') %}
tmux-{{ app }}-segment:
  file.managed:
    - name: /home/{{ pillar['login_user'] }}/tmux-powerline/segments/{{ app }}.sh
    - source: salt://tmux/pid-segment.tmpl.sh
    - template: jinja
    - user: {{ pillar['login_user'] }}
    - context:
        component_name: {{ app }}
    - require:
      - cmd: dotfiles-install-tmux
      - git: tmux-powerline-install
{% endfor %}
