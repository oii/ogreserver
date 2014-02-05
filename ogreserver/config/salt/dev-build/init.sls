include:
  - compass
  - watchdog

extend:
  gunicorn-config:
    file.managed:
      - context:
          bind_hostname: "0.0.0.0"
          gunicorn_port: {{ pillar['gunicorn_port'] }}
          worker_class: sync
          timeout: 300
          loglevel: info

  supervisor-config:
    file.managed:
      - context:
          socket_mode: 0777

  supervisor-log-dir:
    file.directory:
      - user: {{ pillar['login_user'] }}

  supervisor-init-script:
    file.managed:
      - user: {{ pillar['login_user'] }}

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

  ogreserver-service:
    supervisord.running:
      - require_in:
        - supervisord: watchdog-service


logs-chown:
  file.directory:
    - name: /var/log/{{ pillar['app_name'] }}
    - recurse:
      - user
      - group
    - user: {{ pillar['login_user'] }}
    - group: {{ pillar['login_user'] }}
    - require:
      - supervisord: ogreserver-service

ogre-create-user:
  cmd.run:
    - name: /home/{{ pillar['app_user'] }}/.virtualenvs/{{ pillar['app_name'] }}/bin/python manage.py create_user {{ pillar['ogre_user_name'] }} {{ pillar['ogre_user_pass'] }} {{ pillar['ogre_user_email'] }}
    - unless: /home/{{ pillar['app_user'] }}/.virtualenvs/{{ pillar['app_name'] }}/bin/python manage.py create_user {{ pillar['ogre_user_name'] }} null null --test
    - cwd: /srv/ogre
    - user: {{ pillar['app_user'] }}
    - require:
      - virtualenv: app-virtualenv
      - cmd: ogre-init

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
