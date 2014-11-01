from __future__ import absolute_import
from __future__ import unicode_literals

import os
import shutil
import subprocess

from xml.dom import minidom

from .exceptions import KindlePrereqsError
from .utils import make_temp_directory

PROVIDERS = ('kindle',)


def find_ebook_providers(prntr, conf, ignore=None):
    if 'providers' not in conf:
        conf['providers'] = {}

    for provider in PROVIDERS:
        # ignore certain providers as determined by --ignore-* params
        if ignore and provider in ignore:
            continue

        # verify previously saved provider paths
        if provider in conf['providers']:
            if os.path.exists(conf['providers'][provider]) is False:
                # if saved path no longer exists, rescan
                conf['providers'][provider] = None
            else:
                # skip already scanned dirs
                continue

        provider_dir = None

        # call provider functions dynamically by platform
        func_name = '_handle_{}_{}'.format(provider, conf['platform'])
        if func_name in globals() and hasattr(globals()[func_name], '__call__'):
            provider_dir = globals()[func_name](prntr)
        else:
            prntr.p('{} not supported for {} books. Contact oii.'.format(conf['platform'], provider))

        if provider_dir is not None:
            conf['providers'][provider] = provider_dir


def _handle_kindle_Darwin(prntr):
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
                return kindle_dir

        except KindlePrereqsError as e:
            prntr.e('Failed extracting Kindle setup', excp=e)
