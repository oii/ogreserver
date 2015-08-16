from __future__ import absolute_import
from __future__ import unicode_literals

import os
import shutil
import subprocess
import urllib
import urlparse

from xml.dom import minidom

from .exceptions import KindlePrereqsError, ADEPrereqsError
from .utils import make_temp_directory


class ProviderFactory:
    @classmethod
    def create(cls, *args, **kwargs):
        return PROVIDERS[args[0]]['class'](**kwargs)

class ProviderBase(object):
    needs_scan = True
    def __init__(self, *args, **kwargs):
        pass

class LibProvider(ProviderBase):
    '''
    A LibProvider contains a single directory containing ebooks

    Class can be instantiated from config module, which means libpath will be supplied
    to the constructor and scan can be skipped
    '''
    libpath = None

    def __init__(self, libpath=None):
        # store the supplied path, if it exists
        if libpath and os.path.exists(libpath) is True:
            self.libpath = libpath
            self.needs_scan = False

class PathsProvider(ProviderBase):
    '''
    A PathsProvider contains a list of direct ebook paths
    '''
    paths = None


PROVIDERS = {
    'kindle': {
        'friendly': 'Amazon Kindle',
        'class': LibProvider,
    },
    'ade': {
        'friendly': 'Adobe Digital Editions',
        'class': PathsProvider,
    },
}


def find_ebook_providers(prntr, conf, ignore=None):
    '''
    Locate any ebook providers on the client machine (ie. Kindle, ADE)
    '''
    if 'providers' not in conf:
        conf['providers'] = {}

    for provider in PROVIDERS.keys():
        # ignore certain providers as determined by --ignore-* params
        if ignore and provider in ignore:
            continue

        # initialise any providers which werent loaded from config
        if provider not in conf['providers']:
            conf['providers'][provider] = ProviderFactory.create(provider)

        if conf['providers'][provider].needs_scan:
            # call provider functions dynamically by platform
            func_name = '_handle_{}_{}'.format(provider, conf['platform'])
            if func_name in globals() and hasattr(globals()[func_name], '__call__'):
                globals()[func_name](prntr, conf['providers'][provider])
            else:
                prntr.p('{} not supported for {} books. Contact oii.'.format(conf['platform'], provider))


def _handle_kindle_Darwin(prntr, provider):
    # search for Kindle on OSX
    plist = os.path.expanduser('~/Library/Containers/com.amazon.Kindle/Data/Library/Preferences/com.amazon.Kindle.plist')

    # check OSX plist file exists
    if not os.path.exists(plist):
        return None

    # parse plist file and extract Kindle ebooks dir
    with make_temp_directory() as tmpdir:
        try:
            plist_tmp_path = os.path.join(tmpdir, 'com.amazon.Kindle.plist')

            # copy plist to temp dir
            shutil.copyfile(plist, plist_tmp_path)

            # convert binary plist file to plain text
            subprocess.check_call('plutil -convert xml1 {}'.format(plist_tmp_path), shell=True)

            # parse XML plist file
            with open(plist_tmp_path, 'r') as f:
                data = f.read()

            # minidom is rubbish; but there's no nextSibling in ElementTree
            dom = minidom.parseString(data)
            for node in dom.getElementsByTagName('key'):
                if node.firstChild.nodeValue == 'User Settings.CONTENT_PATH':
                    kindle_dir = node.nextSibling.nextSibling.firstChild.nodeValue
                    break

            # validate kindle dir
            if os.path.exists(kindle_dir) and os.path.isdir(kindle_dir):
                prntr.p('Found Amazon Kindle ebooks')
                provider.libpath = kindle_dir

        except KindlePrereqsError as e:
            prntr.e('Failed extracting Kindle setup', excp=e)


def _handle_ade_Darwin(prntr, provider):
    # search for ADE on OSX
    manifest_path = os.path.expanduser('~/Documents/Digital Editions')

    # check OSX ADE path exists
    if not os.path.exists(manifest_path):
        return None

    try:
        def parse_manifest(path):
            # parse XML plist file
            with open(path, 'r') as f:
                data = f.read()

            # minidom is rubbish; but there's no nextSibling in ElementTree
            dom = minidom.parseString(data)
            el = next(iter(dom.getElementsByTagName('dp:content')), None)

            if el is not None:
                p = urlparse.urlparse(el.getAttribute('href'))
                return urllib.unquote(
                    os.path.abspath(os.path.join(p.netloc, p.path))
                )

        provider.paths = []

        for root, _, files in os.walk(manifest_path):
            for filename in files:
                if filename.endswith('.xml'):
                    path = parse_manifest(os.path.join(root, filename))
                    if path is not None:
                        provider.paths.append(
                            (path, os.path.splitext(path)[1][1:])
                        )

        prntr.p('Found Adobe Digital Editions ebooks')

    except ADEPrereqsError as e:
        prntr.e('Failed extracting ADE setup', excp=e)
