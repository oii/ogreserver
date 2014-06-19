from __future__ import absolute_import

import argparse
import getpass
import importlib
import json
import os
import subprocess
import sys
import urllib

from . import __version__

from .core import authenticate, sync, OGRESERVER, metadata_extract
from .utils import make_temp_directory

from .exceptions import OgreException
from .exceptions import AuthDeniedError, AuthError, NoEbooksError, NoUploadsError
from .exceptions import BaconError, MushroomError, SpinachError

from .printer import CliPrinter


def entrypoint():
    ret = False

    try:
        # setup and run argparse
        args = parse_command_line()

        # set default hostname
        if 'host' not in args or args.host is None:
            args.host = OGRESERVER

        # global CLI printer
        prntr = CliPrinter(debug=args.debug if 'args' in args else False)

        # run some checks and create some config variables
        conf = prerequisites(args, prntr)

        if conf is not None:
            ret = main(conf, args, prntr)

    except OgreException as e:
        prntr.e('An exception occurred in ogreclient', excp=e)
        sys.exit(1)

    # exit with return code
    if type(ret) is bool:
        ret = True if ret == 0 else False
    sys.exit(ret)


def parse_command_line():
    parser = argparse.ArgumentParser(
        description='O.G.R.E. client application'
    )
    subparsers = parser.add_subparsers()

    # print the current sesame version
    parser.add_argument(
        '--version', action='version',
        version='sesame {}'.format(__version__),
        help='Print the current Sesame version')

    parent_parser = argparse.ArgumentParser(add_help=False)

    # setup parser for sync command
    psync = subparsers.add_parser('sync',
        parents=[parent_parser],
        help='Synchronise with the OGRE server',
    )
    psync.set_defaults(mode='sync')
    psync.add_argument(
        '--ebook-home', '-H',
        help=('The directory where you keep your ebooks. '
              'You can also set the environment variable $EBOOK_HOME'))

    psync.add_argument(
        '--no-drm', action='store_true',
        help="Disable DRM removal during sync; don't install DeDRM tools")

    psync.add_argument(
        '--verbose', '-v', action='store_true',
        help='Produce lots of output')
    psync.add_argument(
        '--debug', action='store_true',
        help='Print debug information on error')
    psync.add_argument(
        '--quiet', '-q', action='store_true',
        help="Don't produce any output")
    psync.add_argument(
        '--dry-run', '-d', action='store_true',
        help="Dry run the sync; don't actually upload anything to the server")

    # setup parser for update command
    pupdate = subparsers.add_parser('update',
        parents=[parent_parser],
        help='Install the latest DeDRM tools',
    )
    pupdate.set_defaults(mode='update')

    # set ogreserver params which apply to sync & update
    for p in (psync, pupdate):
        p.add_argument(
            '--host',
            help='Override the default server host of oii.ogre.yt')
        p.add_argument(
            '--username', '-u',
            help=('Your O.G.R.E. username. '
                  'You can also set the environment variable $EBOOK_USER'))
        p.add_argument(
            '--password', '-p',
            help=('Your O.G.R.E. password. '
                  'You can also set the environment variable $EBOOK_PASS'))

    # setup parser for dedrm command
    pdedrm = subparsers.add_parser('dedrm',
        parents=[parent_parser],
        help='Strip a single ebook of DRM',
    )
    pdedrm.set_defaults(mode='dedrm')
    pdedrm.add_argument(
        'inputfile',
        help='Ebook to be decrypted')
    pdedrm.add_argument(
        '-O', '--output-dir', default=os.getcwd(),
        help='Extract files into a specific directory')

    # setup parser for info command
    pinfo = subparsers.add_parser('info',
        parents=[parent_parser],
        help="Display an ebook's info",
    )
    pinfo.set_defaults(mode='info')
    pinfo.add_argument(
        'inputfile',
        help='Ebook for which to display info')

    args = parser.parse_args()

    if args.mode == 'sync' and args.verbose and args.quiet:
        parser.error('You cannot specify --verbose and --quiet together!')

    return args


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


def main(conf, args, prntr):
    if args.mode == 'update':
        ebook_home, username, password = validate_input(args)
        ret = download_dedrm(args.host, username, password, prntr)

    elif args.mode == 'info':
        # display metadata from a single book
        ret = display_info(conf, args, prntr, args.inputfile)

    elif args.mode == 'dedrm':
        # decrypt a single book
        ret = dedrm_single_ebook(conf, args, prntr, args.inputfile, args.output_dir)

    elif args.mode == 'sync':
        # run ogreclient
        ebook_home, username, password = validate_input(args)
        ret = run_sync(conf, args, prntr, ebook_home, username, password, debug=args.debug)

    return ret


def dedrm_single_ebook(conf, args, prntr, inputfile, output_dir=None):
    filename, ext = os.path.splitext(inputfile)
    from .dedrm import decrypt, DRM, DecryptionError

    try:
        prntr.p('Decrypting ebook {}'.format(os.path.basename(inputfile)), mode=prntr.DEDRM)

        with make_temp_directory() as ebook_convert_path:
            state, decrypted_filename = decrypt(
                inputfile, ext, ebook_convert_path, conf['config_dir'], output_dir
            )
            if output_dir:
                decrypted_filename = os.path.join(output_dir, decrypted_filename)

            prntr.p('Book decrypted at {}'.format(decrypted_filename), success=True)

    except DecryptionError as e:
        prntr.p(str(e))
        state = None

    if state == DRM.decrypted:
        return 0
    else:
        return 1


def display_info(conf, args, prntr, filepath):
    meta = metadata_extract(conf['calibre_ebook_meta_bin'], filepath)
    prntr.p('Book meta', extra=meta)


def run_sync(conf, args, prntr, ebook_home, username, password, debug=False):
    ret = False

    # setup config for sync
    conf.update({
        'ebook_home': ebook_home,
        'username': username,
        'password': password,
        'host': args.host,
        'verbose': args.verbose,
        'quiet': args.quiet,
        'no_drm': args.no_drm,
    })

    try:
        # doit
        ret = sync(conf)

    # print messages on error
    except (AuthError, BaconError, MushroomError, SpinachError) as e:
        prntr.e('Something went wrong.', excp=e)
    except AuthDeniedError:
        prntr.e('Permission denied. This is a private system.')
    except NoEbooksError:
        prntr.e('No ebooks found. Pass --ebook-home or set $EBOOK_HOME.')
    except NoUploadsError:
        prntr.e('Nothing to upload..')
    except Exception as e:
        prntr.e('Something very went wrong.', excp=e)

    return ret


# TODO write tests for the prerequistes
def prerequisites(args, prntr):
    first_scan_warning = False

    # setup some ebook cache file paths
    config_dir = os.path.join(os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), 'ogre')
    ebook_cache_path = os.path.join(config_dir, 'ebook_cache')

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
            # locate calibre's binaries
            calibre_ebook_meta_bin = subprocess.check_output('which ebook-meta', shell=True).strip()
        except subprocess.CalledProcessError:
            try:
                calibre_ebook_meta_bin = subprocess.check_output(
                    'find /Applications/Calibre.app -type f -name ebook-meta', shell=True
                ).strip()
            except subprocess.CalledProcessError:
                pass

        if len(calibre_ebook_meta_bin) == 0:
            prntr.e('You must install Calibre in order to use ogreclient.')
            prntr.e('Please follow the simple instructions at http://ogre.oii.yt/install')
            sys.exit(1)

        conf = {
            'calibre_ebook_meta_bin': calibre_ebook_meta_bin
        }

        with open(os.path.join(config_dir, 'app.config'), 'w') as f_config:
            f_config.write(json.dumps(conf))

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
            installed = download_dedrm(args.host, username, password, prntr)

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
    conf['ebook_cache_path'] = ebook_cache_path
    return conf


def download_dedrm(host, username, password, prntr):
    prntr.p('Downloading latest DRM tools from {}'.format(host))

    try:
        # authenticate with ogreserver to get DRM tools
        session_key = authenticate(host, username, password)

    except (AuthError, AuthDeniedError) as e:
        prntr.e('Permission denied. This is a private system.')
        return None
    except (AuthError, AuthDeniedError) as e:
        prntr.e("Couldn't get DRM tools", excp=e)
        return False

    prntr.p('Authenticated with Ogreserver')
    prntr.p('Downloading..')

    # download the tarball
    urllib.urlretrieve(
        'http://{}/download-dedrm/{}'.format(host, session_key),
        '/tmp/dedrm.tar.gz',
        prntr.progressf
    )

    try:
        # install DRM tools
        subprocess.check_output('pip install /tmp/dedrm.tar.gz', shell=True)

        # attempt a dynamic load of the newly imported tools
        mod = importlib.import_module('dedrm')

    except subprocess.CalledProcessError as e:
        prntr.e('Failed installing dedrm tools', excp=e)
        return False
    except ImportError as e:
        prntr.e('Failed installing dedrm tools', excp=e)
        return False

    prntr.p('Installed dedrm {}'.format(mod.PLUGIN_VERSION))
    return True
