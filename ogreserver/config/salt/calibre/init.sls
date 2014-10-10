calibre-install:
  file.managed:
    - name: /opt/calibre-installer.py
    - source: salt://calibre/linux-installer.py
    - template: jinja
    - mode: 744
    - context:
        version: 2.9.0
  cmd.wait:
    - name: /opt/calibre-installer.py
    - watch:
      - file: calibre-install

# support packages for ebook-meta
calibre-pkgs:
  pkg.installed:
    - names:
      - fontconfig
      - libxt6
      - libxi6
      - libxrender1
      - libxrandr2
      - libxfixes3
      - libxcursor1
