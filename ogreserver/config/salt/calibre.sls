calibre-install:
  archive.extracted:
    - name: /opt/calibre
    - source: https://s3-eu-west-1.amazonaws.com/calibre-binary-mirror/calibre-2.80.0-x86_64.txz
    - source_hash: sha1=730ed279581b9546b18580fef671894702645076
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
