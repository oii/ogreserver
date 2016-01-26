newrelic:
  pip:
    - installed
  cmd.run:
    - name: newrelic-admin generate-config {{ pillar.get('newrelic_key', 'MISSING_KEY') }} /etc/newrelic.ini
    - watch:
      - pip: newrelic

newrelic-config:
  file.managed:
    - name: /etc/newrelic.ini
    - user: {{ pillar['app_user'] }}
    - group: {{ pillar['app_user'] }}
    - mode: 640
    - require:
      - cmd: newrelic

newrelic-pkgrepo:
  pkgrepo.managed:
    - humanname: Newrelic PPA
    - name: deb http://apt.newrelic.com/debian/ newrelic non-free
    - file: /etc/apt/sources.list.d/newrelic.list
    - key_url: https://download.newrelic.com/548C16BF.gpg
    - require_in:
      - pkg: newrelic-sysmond

newrelic-sysmond:
  pkg:
    - installed
  cmd.run:
    - name: nrsysmond-config --set license_key={{ pillar.get('newrelic_key', 'MISSING_KEY') }}
    - watch:
      - pkg: newrelic-sysmond
  service.running:
    - require:
      - pkg: newrelic-sysmond
