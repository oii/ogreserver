from __future__ import absolute_import
from __future__ import unicode_literals

import ConfigParser
import os

from .providers import PROVIDERS


def _get_config_dir():
    # setup config dir path
    return os.path.join(os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), 'ogre')


def write_config(conf):
    cp = ConfigParser.RawConfigParser()

    # general config section
    cp.add_section('config')
    if 'calibre_ebook_meta_bin' in conf:
        cp.set('config', 'calibre_ebook_meta_bin', conf['calibre_ebook_meta_bin'])

    # ogreserver specific section
    cp.add_section('ogreserver')
    if 'host' in conf:
        cp.set('ogreserver', 'host', conf['host'])
    if 'username' in conf:
        cp.set('ogreserver', 'username', conf['username'])
    if 'password' in conf:
        cp.set('ogreserver', 'password', conf['password'])

    # create sections for each provider
    for provider in PROVIDERS.keys():
        if provider in conf['providers']:
            cp.add_section(provider)

    with open(os.path.join(conf['config_dir'], 'app.config'), 'wb') as f_config:
        cp.write(f_config)


def read_config():
    conf = {'config_dir': _get_config_dir()}

    if not os.path.exists(conf['config_dir']):
        os.makedirs(conf['config_dir'])
        return conf

    if not os.path.exists(os.path.join(conf['config_dir'], 'app.config')):
        return conf

    cp = ConfigParser.RawConfigParser()

    try:
        cp.read(os.path.join(conf['config_dir'], 'app.config'))
    except ConfigParser.ParsingError:
        return conf

    conf['calibre_ebook_meta_bin'] = cp.get('config', 'calibre_ebook_meta_bin')
    conf['host'] = cp.get('ogreserver', 'host')
    conf['username'] = cp.get('ogreserver', 'username')
    conf['password'] = cp.get('ogreserver', 'password')

    # extract which providers are already known (used for CLI options)
    for provider in PROVIDERS.keys():
        if cp.has_section(provider):
            conf['has_{}'.format(provider)] = True

    return conf
