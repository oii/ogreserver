from __future__ import absolute_import

import argparse
import getpass
import json
import os
import subprocess
import sys
import urllib

from . import __version__
from . import OgreError

from .core import authenticate, doit, last_error, OGRESERVER, PROGBAR_LEN, RETURN_CODES
from .utils import make_temp_directory, update_progress, CliPrinter


def entrypoint():
    try:
        # setup and run argparse
        args = parse_command_line()

        # set default hostname
        if 'host' not in args or args.host is None:
            args.host = OGRESERVER

        # global printer for init phase
        prntr = CliPrinter(None)

        # run some checks and create some config variables
        conf = prerequisites(args, prntr)

        if args.mode == 'update':
            ebook_home, username, password = validate_input(args)
            ret = download_dedrm(args.host, username, password, prntr)

        elif args.mode == 'dedrm':
            # decrypt a single book
            ret = dedrm_single_ebook(conf, args, prntr, args.inputfile, args.output_dir)

        elif args.mode == 'sync':
            # run ogreclient
            ebook_home, username, password = validate_input(args)
            ret = main(conf, args, ebook_home, username, password)

    except OgreError as e:
        sys.stderr.write('{}\n'.format(e))
        sys.stderr.flush()
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
        '--verbose', '-v', action='store_true',
        help='Produce lots of output')
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


def dedrm_single_ebook(conf, args, prntr, inputfile, output_dir=None):
    filename, ext = os.path.splitext(inputfile)
    from .dedrm import decrypt, DRM, DecryptionError

    try:
        with make_temp_directory() as ebook_convert_path:
            state, decrypted_filename = decrypt(
                inputfile, ext, ebook_convert_path, conf['config_dir'], output_dir
            )
            if output_dir:
                decrypted_filename = os.path.join(output_dir, decrypted_filename)

            prntr.p('Book decrypted at {}'.format(decrypted_filename))

    except DecryptionError as e:
        prntr.p(str(e))
        state = None

    if state == DRM.decrypted:
        return 0
    else:
        return 1


def main(conf, args, ebook_home, username, password):
    # setup a temp path for DRM checks with ebook-convert
    with make_temp_directory() as ebook_convert_path:
        ret = doit(
            ebook_home=ebook_home,
            username=username,
            password=password,
            host=args.host,
            config_dir=conf['config_dir'],
            ebook_cache_path=conf['ebook_cache_path'],
            ebook_cache_temp_path=conf['ebook_cache_temp_path'],
            ebook_convert_path=ebook_convert_path,
            calibre_ebook_meta_bin=conf['calibre_ebook_meta_bin'],
            verbose=args.verbose,
            quiet=args.quiet,
        )

    # print messages on error
    if ret > 0:
        if ret == RETURN_CODES.error_auth:
            msg = 'Something went wrong, contact tha spodz with..\nCode egg: {}'.format(last_error)
        elif ret == RETURN_CODES.error_bacon:
            msg = 'Something went wrong, contact tha spodz with..\nCode bacon: {}'.format(last_error)
        elif ret == RETURN_CODES.error_mushroom:
            msg = 'Something went wrong, contact tha spodz with..\nCode mushroom: {}'.format(last_error)
        elif ret == RETURN_CODES.error_spinach:
            msg = 'Something went wrong, contact tha spodz with..\nCode spinach: {}'.format(last_error)
        elif ret == RETURN_CODES.auth_denied:
            msg = 'Permission denied. This is a private system.'
        elif ret == RETURN_CODES.no_ebooks:
            msg = 'No ebooks found. Is $EBOOK_HOME set correctly?'
        elif ret == RETURN_CODES.no_uploads:
            msg = 'Nothing to upload..'

        sys.stderr.write('{}\n'.format(msg))

    return ret


def prerequisites(args, prntr):
    # setup some ebook cache file paths
    config_dir = os.path.join(os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config')), 'ogre')
    ebook_cache_path = os.path.join(config_dir, 'ebook_cache')
    ebook_cache_temp_path = os.path.join(config_dir, 'ebook_cache.tmp')

    # use existing config if available
    if os.path.exists(config_dir) and os.path.exists(os.path.join(config_dir, 'app.config')):
        with open(os.path.join(config_dir, 'app.config'), 'r') as f_config:
            conf = json.loads(f_config.read())

    # create a config directory in $HOME on first run
    elif not os.path.exists(config_dir):
        prntr.p('Please note that DRM scanning means the first run of ogreclient '
                'will be much slower than subsequent runs.', notime=True)

        os.makedirs(config_dir)

        # locate calibre's binaries
        try:
            calibre_ebook_meta_bin = subprocess.check_output(
                ['find', '/Applications', '-type', 'f', '-name', 'ebook-meta']
            ).strip()

            if len(calibre_ebook_meta_bin) == 0:
                raise Exception
        except:
            sys.stderr.write('You must install calibre in order to use ogreclient.')
            sys.stderr.write('Please follow the simple instructions at http://ogre.oii.yt/install')
            sys.exit(1)

        conf = {
            'calibre_ebook_meta_bin': calibre_ebook_meta_bin
        }

        with open(os.path.join(config_dir, 'app.config'), 'w') as f_config:
            f_config.write(json.dumps(conf))

    # check if we have decrypt capability
    from .dedrm import CAN_DECRYPT

    if CAN_DECRYPT is False:
        ebook_home, username, password = validate_input(args)

        # attempt to download and setup dedrm
        attempted_download = True
        download_dedrm(args.host, username, password, prntr)
    else:
        attempted_download = False

    # initialise dedrm lib
    from .dedrm import init_keys

    if CAN_DECRYPT is True:
        from dedrm import PLUGIN_VERSION
        prntr.p('Initialized DRM tools v{}'.format(PLUGIN_VERSION))

        msgs = init_keys(config_dir, ignore_check=True)
        for m in msgs:
            prntr.p(m)

    elif attempted_download is True:
        prntr.e('Failed to download DRM tools. Please report this error.', notime=True)

    # return config object
    conf['config_dir'] = config_dir
    conf['ebook_cache_path'] = ebook_cache_path
    conf['ebook_cache_temp_path'] = ebook_cache_temp_path
    return conf


def download_dedrm(host, username, password, prntr):
    prntr.p('Downloading latest DRM tools from {}'.format(host))

    # retrieve the DRM tools
    session_key = authenticate(host, username, password)

    if type(session_key) is not str:
        prntr.p("Couldn't get DRM tools")
        return False
    elif verbose:
        prntr.p('Authenticated with Ogreserver. Downloading..')

    # download the tarball
    urllib.urlretrieve(
        'http://{}/download-dedrm/{}'.format(host, session_key),
        '/tmp/dedrm.tar.gz',
        dl_progress
    )

    # install DRM tools
    subprocess.check_output('pip install /tmp/dedrm.tar.gz', shell=True)
    prntr.p('Installed dedrm latest')
    return True


def dl_progress(count, size, total):
    progress = float(count * size) / float(total)
    update_progress(progress if progress < 1 else 1, length=PROGBAR_LEN)
