extend:
  datadog-service:
    service.running:
      - watch:
        - file: /etc/dd-agent/conf.d/postgres.yaml


create-postgres-datadog-user:
  postgres_user.present:
    - name: datadog
    - password: datadog
    - require:
      - service: postgresql

#create-postgres-datadog-privileges:
#  postgres_privileges.present:
#    - name: pg_stat_database
#    - object_name: ALL
#    - object_type: schema
#    - privileges:
#      - SELECT
#    - require:
#      - postgres_user: create-postgres-datadog-user
#
/etc/dd-agent/conf.d/postgres.yaml:
  file.managed:
    - contents: |
        init_config:
        instances:
          - host: localhost
            port: 5432
            username: datadog
            password: datadog
            tags:
              app: ogreserver
              env: dev
            collect_count_metrics: false
    - require:
      - pkg: datadog-agent
