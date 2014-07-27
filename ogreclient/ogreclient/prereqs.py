from __future__ import absolute_import

import getpass
import json
import os
import subprocess
import sys

from .cache import Cache
from .dedrm import download_dedrm


def setup(args, prntr):
    first_scan_warning = False

    # setup some ebook cache file paths
    config_dir = os.path.join(os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), 'ogre')
    ebook_cache = Cache(os.path.join(config_dir, 'ebook_cache.db'))

    # use existing config if available
    if os.path.exists(config_dir) and os.path.exists(os.path.join(config_dir, 'app.config')):
        with open(os.path.join(config_dir, 'app.config'), 'r') as f_config:
            conf = json.loads(f_config.read())

    # create a config directory in $HOME on first run
    elif not os.path.exists(config_dir) or not os.path.exists(os.path.join(config_dir, 'app.config')):
        first_scan_warning = True

        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        calibre_ebook_meta_bin = ''

        try:
            # locate calibre's binaries with shell
            calibre_ebook_meta_bin = subprocess.check_output('which ebook-meta', shell=True).strip()
        except subprocess.CalledProcessError:
            # filesystem search
            if os.path.exists('/Applications/Calibre.app'):
                try:
                    calibre_ebook_meta_bin = subprocess.check_output(
                        'find /Applications/Calibre.app -type f -name ebook-meta', shell=True
                    ).strip()
                except subprocess.CalledProcessError:
                    pass

        # ogreclient requires calibre (unfortunately)
        if len(calibre_ebook_meta_bin) == 0:
            prntr.e('You must install Calibre in order to use ogreclient.')
            prntr.e('Please follow the simple instructions at http://ogre.oii.yt/install')
            sys.exit(1)

        conf = {
            'calibre_ebook_meta_bin': calibre_ebook_meta_bin
        }

        # write the config file for first time
        with open(os.path.join(config_dir, 'app.config'), 'w') as f_config:
            f_config.write(json.dumps(conf))


    # verify the ogreclient cache; true means it was initialised
    if ebook_cache.verify_cache(prntr):
        first_scan_warning = True


    if args.mode == 'sync' and args.no_drm is True:
        # skip drm check
        pass
    else:
        # check if we have decrypt capability
        from .dedrm import CAN_DECRYPT

        if CAN_DECRYPT is False:
            ebook_home, username, password = validate_input(args)

            # attempt to download and setup dedrm
            attempted_download = True
            installed = download_dedrm(args.host, username, password, prntr, debug=args.debug)

            if installed is None:
                # auth failed contacting ogreserver
                return
        else:
            attempted_download = False
            installed = False

        from .dedrm import init_keys

        # initialise a working dedrm lib
        if CAN_DECRYPT is True or installed is True:
            msgs = init_keys(config_dir, ignore_check=True)
            for m in msgs:
                prntr.p(m)

            from dedrm import PLUGIN_VERSION
            prntr.p('Initialised DRM tools v{}'.format(PLUGIN_VERSION))

        elif attempted_download is True:
            prntr.e('Failed to download DRM tools. Please report this error.')

    if first_scan_warning is True:
        prntr.p('Please note that DRM scanning means the first run of ogreclient '
                'will be much slower than subsequent runs.')

    # return config object
    conf['config_dir'] = config_dir
    conf['ebook_cache'] = ebook_cache
    return conf


def validate_input(args):
    if 'ebook_home' in args:
        ebook_home = args.ebook_home
    else:
        ebook_home = None

    username = args.username
    password = args.password

    # setup the environment
    if ebook_home is None:
        ebook_home = os.getenv('EBOOK_HOME')
        if ebook_home is None or len(ebook_home) == 0:
            print 'You must supply --ebook-home or set the $EBOOK_HOME environment variable'
            sys.exit(1)

    if username is None:
        username = os.getenv('EBOOK_USER')
        if username is None or len(username) == 0:
            username = getpass.getuser()
            if username is not None:
                print "$EBOOK_USER is not set. Please enter your username, or press enter to use '{}':".format(username)
                ri = raw_input()
                if len(ri) > 0:
                    username = ri

        if username is None:
            print '$EBOOK_USER is not set. Please enter your username, or press enter to exit:'
            username = raw_input()
            if len(username) == 0:
                sys.exit(1)

    if password is None:
        password = os.getenv('EBOOK_PASS')
        if password is None or len(password) == 0:
            print '$EBOOK_PASS is not set. Please enter your password, or press enter to exit:'
            password = getpass.getpass()
            if len(password) == 0:
                sys.exit(1)

    return ebook_home, username, password
