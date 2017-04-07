extend:
  datadog-service:
    service.running:
      - watch:
        - file: /etc/dd-agent/conf.d/nginx.yaml


/etc/dd-agent/conf.d/nginx.yaml:
  file.managed:
    - contents: |
        init_config:
        instances:
          - nginx_status_url: http://{{ grains['ip_interfaces']['eth0'][0] }}/nginx_status/
            tags:
              app: ogreserver
              env: dev
    - require:
      - pkg: datadog-agent
