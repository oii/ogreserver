def compute_md5(fp, buf_size=8192):
    """
    Straight lifted from boto/utils.py in boto HEAD
    """
    m = md5()
    fp.seek(0)
    s = fp.read(buf_size)
    while s:
        m.update(s)
        s = fp.read(buf_size)

    hex_md5 = m.hexdigest()
    base64md5 = base64.encodestring(m.digest())

    if base64md5[-1] == '\n':
        base64md5 = base64md5[0:-1]

    file_size = fp.tell()
    fp.seek(0)
    return (hex_md5, base64md5, file_size)
