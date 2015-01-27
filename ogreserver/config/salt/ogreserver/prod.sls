include:
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
          server_name: ogre.oii.yt
          root: /srv/{{ pillar['app_directory_name'] }}/ogreserver
          upstream_gzip: true
  {% endfor %}


# install SSL certificate
/etc/ssl/ogre.oii.yt.crt:
  file.managed:
    - contents_pillar: ssl:cert
    - require_in:
      - service: nginx

/etc/ssl/ogre.oii.yt.key:
  file.managed:
    - contents_pillar: ssl:key
    - require_in:
      - service: nginx

# compress js to gzip
javascript-compile:
  cmd.run:
    - name: closure-compiler --output-format gzip app.js
    - cwd: /srv/{{ pillar['app_directory_name'] }}/ogreserver/static/js
    - user: {{ pillar['app_user'] }}
    - require:
      - git: git-clone-app

gevent:
  pip.installed:
    - bin_env: /home/{{ pillar['app_user'] }}/.virtualenvs/{{ pillar['app_name'] }}
    - user: {{ pillar['app_user'] }}
    - require_in:
      - service: supervisor
