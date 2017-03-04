postgresql-pkgrepo:
  pkgrepo.managed:
    - humanname: PostgreSQL
    - name: deb http://apt.postgresql.org/pub/repos/apt/ {{ grains['oscodename'] }}-pgdg main
    - file: /etc/apt/sources.list.d/pgdg.list
    - key_url: https://www.postgresql.org/media/keys/ACCC4CF8.asc
    - require_in:
      - pkg: postgresql

postgresql:
  pkg.installed:
    - names:
      - postgresql-9.6
      - postgresql-client-9.6
  service.running:
    - enable: true
    - require:
      - pkg: postgresql


create-postgres-user:
  postgres_user.present:
    - name: {{ pillar['db_user'] }}
    - password: {{ pillar['db_pass'] }}
    - login: true
    - require:
      - service: postgresql

create-postgres-db:
  postgres_database.present:
    - name: {{ pillar['db_name'] }}
    - owner: {{ pillar['db_user'] }}
    - require:
      - postgres_user: create-postgres-user

create-postgres-privileges:
  postgres_privileges.present:
    - name: {{ pillar['db_user'] }}
    - object_name: ALL
    - object_type: table
    - privileges:
      - SELECT
      - INSERT
      - UPDATE
      - DELETE
    - require:
      - postgres_database: create-postgres-db
