{% if grains['saltversion'].startswith("0.17.5") %}

/usr/lib/python2.7/dist-packages/salt/states/supervisord.py:
  file.managed:
    - source: salt://salt-backports/supervisord.0-17-5.state.py

/usr/lib/python2.7/dist-packages/salt/modules/supervisord.py:
  file.managed:
    - source: salt://salt-backports/supervisord.0-17-5.module.py
    - require:
      - file: /usr/lib/python2.7/dist-packages/salt/states/supervisord.py

salt-hack-restart:
  cmd.run:
    - name: service salt-minion restart
    - watch:
      - file: /usr/lib/python2.7/dist-packages/salt/modules/supervisord.py
    - order: 1

{% endif %}
