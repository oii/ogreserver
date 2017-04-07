include:
  - datadog.gunicorn
  - datadog.nginx
  - datadog.postgres


datadog-apt-reqs:
  pkg.installed:
    - names:
      - libcurl3-gnutls
      - apt-transport-https

datadog-pkgrepo:
  pkgrepo.managed:
    - humanname: Datadog
    - name: deb https://apt.datadoghq.com/ stable main
    - file: /etc/apt/sources.list.d/datadog.list
    - keyid: C7A7DA52
    - keyserver: keyserver.ubuntu.com

datadog-agent:
  pkg.installed:
    - require:
      - pkgrepo: datadog-pkgrepo

datadog-config:
  file.copy:
    - name: /etc/dd-agent/datadog.conf
    - source: /etc/dd-agent/datadog.conf.example
    - require:
      - pkg: datadog-agent

datadog-config-api-key:
  file.line:
    - name: /etc/dd-agent/datadog.conf
    - content: 'api_key: {{ pillar.get('datadog_api_key', '') }}'
    - match: 'api_key:'
    - mode: replace
    - require:
      - file: datadog-config

{% if pillar.get('datadog_tags', '') %}
datadog-config-tags:
  file.line:
    - name: /etc/dd-agent/datadog.conf
    - content: 'tags: {{ pillar.get('datadog_tags', '') }}'
    - match: '# tags:.*'
    - mode: replace
    - require:
      - file: datadog-config
{% endif %}

datadog-service:
  service.running:
    - name: datadog-agent
    - enable: true
