include:
  - ruby


compass-gem:
  gem.installed:
    - name: compass
    - require:
      - cmd: ruby-dev

compass-supervisor-config:
  file.managed:
    - name: /etc/supervisor/conf.d/compass.{{ pillar['app_name'] }}.conf
    - source: salt://compass/supervisord.conf
    - template: jinja
    - defaults:
        watch_directory: /srv/{{ pillar['app_name'] }}
        app_name: {{ pillar['app_name'] }}
        app_user: {{ pillar['app_user'] }}
    - require:
      - gem: compass-gem
    - require_in:
      - service: supervisor

compass-supervisor-service:
  supervisord.running:
    - name: compass
    - update: true
    - require:
      - service: supervisor
    - watch:
      - file: compass-supervisor-config
