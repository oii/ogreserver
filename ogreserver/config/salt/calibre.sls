calibre-install:
  archive.extracted:
    - name: /opt/calibre
    - source: https://github.com/kovidgoyal/calibre/releases/download/v2.72.0/calibre-2.72.0-x86_64.txz
    - source_hash: sha1=869d92c8d63a215a65f139b05ef61080616ac9b6
    - archive_format: tar
  cmd.wait:
    - name: /opt/calibre/calibre_postinstall
    - watch:
      - archive: calibre-install

# required packages for ebook-meta & ebook-convert
calibre-pkgs:
  pkg.installed:
    - names:
      - libltdl7
      - python-pyqt5
