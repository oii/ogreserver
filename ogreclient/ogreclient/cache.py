from __future__ import absolute_import

import json
import os
import sqlite3

from .exceptions import OgreException

__CACHEVERSION__ = 1


class Cache:
    def __init__(self, ebook_cache_path):
        self.ebook_cache_path = ebook_cache_path


    def verify_cache(self, prntr):
        must_init_cache = False

        if os.path.exists(self.ebook_cache_path):
            conn = None
            try:
                # check the cache is valid
                conn = sqlite3.connect(self.ebook_cache_path)
                c = conn.cursor()
                c.execute('SELECT version FROM meta LIMIT 1')

                # if no exception thus far, check the cache version
                version = c.fetchone()[0]
                if version < __CACHEVERSION__:
                    # migrate cache model as upgrade path
                    self.cache_migrate(version, __CACHEVERSION__)

            except:
                prntr.e('Cache file corrupt! Recreating as per first run..')
                must_init_cache = True
            finally:
                if conn is not None:
                    conn.close()
        else:
            # first create of cache db
            must_init_cache = True

        if must_init_cache:
            # create the sqlite cache
            self.init_cache()

        return must_init_cache


    def cache_migrate(self, from_version, to_version):
        pass


    def init_cache(self):
        conn = sqlite3.connect(self.ebook_cache_path)
        try:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE ebooks (
                      path TEXT PRIMARY KEY,
                      file_hash TEXT NULL,
                      data TEXT NULL,
                      drmfree INT DEFAULT 0,
                      skip INT DEFAULT 0
                )'''
            )
            c.execute('CREATE TABLE meta (version INT PRIMARY KEY)')
            conn.commit()
            c.execute('INSERT INTO meta VALUES (?)', (__CACHEVERSION__,))
            conn.commit()
        except:
            raise CacheInitError
        finally:
            conn.close()


    def get_ebook(self, path, file_hash=None):
        conn = sqlite3.connect(self.ebook_cache_path)
        try:
            c = conn.cursor()
            c.execute('SELECT file_hash, data, drmfree, skip FROM ebooks WHERE path = ?', (path,))
            obj = c.fetchone()
            if obj is not None:
                # verify file_hash matches between cache and filesystem
                if file_hash is not None and obj[0] != file_hash:
                    c.execute('DELETE FROM ebooks WHERE path = ?', (path,))
                    conn.commit()
                else:
                    return obj[1], obj[2], obj[3]
        except Exception as e:
            raise CacheReadError(e)
        finally:
            conn.close()

        return None, None, None


    def set_ebook(self, path, file_hash=None, data=None, drmfree=False, skip=False):
        conn = sqlite3.connect(self.ebook_cache_path)
        try:
            c = conn.cursor()
            c.execute('SELECT drmfree FROM ebooks WHERE path = ?', (path,))
            obj = c.fetchone()
            # update if exists, otherwise insert
            if obj is not None:
                values = ''
                params = []

                # build update parameter list
                if file_hash is not None:
                    values += 'file_hash = ?, '
                    params.append(file_hash)
                if data is not None:
                    values += 'data = ?, '
                    params.append(json.dumps(data))

                if drmfree is not None:
                    values += 'drmfree = ?, '
                    params.append(int(drmfree))

                if skip is not None:
                    values += 'skip = ?'
                    params.append(int(skip))

                # where path
                params.append(path)

                c.execute(
                    'UPDATE ebooks SET {} WHERE path = ?'.format(values), params
                )
            else:
                c.execute(
                    'INSERT INTO ebooks VALUES (?,?,?,?,?)',
                    (path, file_hash, json.dumps(data), int(drmfree), int(skip))
                )
            conn.commit()
        except Exception as e:
            raise CacheReadError(e)
        finally:
            conn.close()


class CacheInitError(OgreException):
    pass

class CacheReadError(OgreException):
    pass

class CacheWriteError(OgreException):
    pass
