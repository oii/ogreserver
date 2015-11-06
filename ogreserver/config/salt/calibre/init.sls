calibre-install:
  file.managed:
    - name: /opt/calibre-installer.py
    - source: salt://calibre/linux-installer.py
    - template: jinja
    - mode: 744
    - context:
        version: 2.43.0
  cmd.wait:
    - name: /opt/calibre-installer.py
    - watch:
      - file: calibre-install

# required packages for ebook-meta & ebook-convert
calibre-pkgs:
  pkg.installed:
    - names:
      - libltdl7
      - python-pyqt5
