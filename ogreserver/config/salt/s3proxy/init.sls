s3proxy-dependencies:
  pkg.installed:
    - names:
      - openjdk-7-jre-headless

s3proxy-install:
  file.managed:
    - name: /usr/local/bin/s3proxy
    - source: https://github.com/andrewgaul/s3proxy/releases/download/s3proxy-1.0.0/s3proxy
    - source_hash: sha1=9a6de7b37d6ff8e4b45401f6c0ce0025e399f2b8
  cmd.wait:
    - name: chmod u+x /usr/local/bin/s3proxy
    - watch:
      - file: s3proxy-install

s3proxy-config:
  file.managed:
    - name: /etc/s3proxy.conf
    - contents: |
        s3proxy.authorization=none
        s3proxy.endpoint=http://127.0.0.1:8880
        jclouds.provider=filesystem
        jclouds.identity=identity
        jclouds.credential=credential
        jclouds.filesystem.basedir=/tmp

s3proxy-supervisor-config:
  file.managed:
    - name: /etc/supervisor/conf.d/s3proxy.conf
    - source: salt://s3proxy/supervisord.conf
    - template: jinja
    - defaults:
        runas: root
    - require:
      - pkg: s3proxy-dependencies
    - require_in:
      - service: supervisor

s3proxy-supervisor-service:
  supervisord.running:
    - name: s3proxy
    - update: true
    - require:
      - pkg: s3proxy-dependencies
      - cmd: s3proxy-install
      - file: s3proxy-config
      - service: supervisor
    - watch:
      - file: s3proxy-supervisor-config
