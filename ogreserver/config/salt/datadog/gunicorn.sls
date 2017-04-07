extend:
  datadog-service:
    service.running:
      - watch:
        - file: /etc/dd-agent/conf.d/gunicorn.yaml


/etc/dd-agent/conf.d/gunicorn.yaml:
  file.managed:
    - contents: |
        init_config:
        instances:
          - proc_name: {{ pillar['app_name'] }}-gunicorn
            tags:
              app: ogreserver
              env: dev
    - require:
      - pkg: datadog-agent
