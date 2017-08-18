calibre-install:
  archive.extracted:
    - name: /opt/calibre
    - source: https://s3-eu-west-1.amazonaws.com/calibre-binary-mirror/calibre-3.2.1-x86_64.txz
    - source_hash: sha1=ed754309762208a9ba6dcbc02974e2a7dfb1588c
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
