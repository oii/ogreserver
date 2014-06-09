rethinkdb-pkgrepo:
  pkgrepo.managed:
    - humanname: RethinkDB PPA
    {% if grains['os'] == "Debian" %}
    - name: deb http://ppa.launchpad.net/rethinkdb/ppa/ubuntu lucid main
    {% elif grains['os'] == "Ubuntu" %}
    - name: deb http://ppa.launchpad.net/rethinkdb/ppa/ubuntu {{ grains['oscodename'] }} main
    {% endif %}
    - file: /etc/apt/sources.list.d/rethinkdb.list
    - keyid: 11D62AD6
    - keyserver: keyserver.ubuntu.com
    - require_in:
      - pkg: rethinkdb

rethinkdb:
  user.present:
    - createhome: false
    - gid_from_name: true
  pkg.installed:
    - version: "1.12.5-0ubuntu1~lucid"


python-pip-rethinkdb:
  pkg.installed:
    - name: python-pip

rethinkdb-python-driver:
  pip.installed:
    - name: rethinkdb
    - require:
      - pkg: python-pip-rethinkdb


rethinkdb-chown-lib:
  file.directory:
    - name: /var/lib/rethinkdb
    - user: rethinkdb
    - group: rethinkdb
    - require:
      - pkg: rethinkdb

rethinkdb-config:
  file.managed:
    - name: /etc/rethinkdb/instances.d/{{ pillar['app_name'] }}.conf
    - source: salt://rethinkdb/rethinkdb.instance.conf
    - template: jinja
    - user: rethinkdb
    - group: rethinkdb
    - defaults:
        app_name: {{ pillar['app_name'] }}
        data_directory: null
        production: true
        host: null
        canonical_address: null
        join: []
    - require:
      - pkg: rethinkdb
      - user: rethinkdb
  cmd.wait:
    - name: /etc/init.d/rethinkdb restart
    - require:
      - file: rethinkdb-chown-lib
    - watch:
      - file: rethinkdb-config
