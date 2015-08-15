from __future__ import absolute_import
from __future__ import unicode_literals

import argparse
import os
import sys

from . import __version__

from .config import read_config
from .core import sync, stats
from .ebook_obj import EbookObject
from .prereqs import setup_ogreclient
from .printer import CliPrinter, DummyPrinter
from .providers import PROVIDERS

from .exceptions import OgreException, ConfigSetupError
from .exceptions import AuthDeniedError, AuthError, NoEbooksError
from .exceptions import SyncError, UploadError


def entrypoint():
    ret = False
    prntr = None

    try:
        # quick config load
        conf = read_config()

        # setup and run argparse
        args = parse_command_line(conf)

        # global CLI printer
        if args.quiet is True:
            prntr = DummyPrinter()
        else:
            prntr = CliPrinter(debug=args.debug)

            # set printer to log everything for later dispatch to ogreserver
            if args.debug is True:
                prntr.log_output = True

        # run some checks and create some config variables
        conf = setup_ogreclient(args, prntr, conf)

        if conf is not None:
            ret = main(conf, args, prntr)

    except ConfigSetupError as e:
        prntr.e('Failed setting up ogreclient', excp=e)
    except OgreException as e:
        prntr.e('An exception occurred in ogreclient', excp=e)
        ret = 1
    finally:
        if prntr is not None:
            # allow the printer to cleanup
            prntr.close()

    # exit with return code
    if type(ret) is bool:
        ret = True if ret == 0 else False
    sys.exit(ret)


def parse_command_line(conf):
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
    parent_parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Produce lots of output')
    parent_parser.add_argument(
        '--debug', action='store_true',
        help='Print debug information on error')
    parent_parser.add_argument(
        '--quiet', '-q', action='store_true',
        help="Don't produce any output")
    parent_parser.add_argument(
        '--skip-cache', action='store_true',
        help='Ignore the local cache; useful for debugging')

    # setup parser for sync command
    psync = subparsers.add_parser('sync',
        parents=[parent_parser],
        help='Synchronise with the OGRE server',
    )
    psync.set_defaults(mode='sync')

    psync.add_argument(
        '--host',
        help='Override the default server host of oii.ogre.yt')
    psync.add_argument(
        '--username', '-u',
        help=('Your O.G.R.E. username. '
              'You can also set the environment variable $EBOOK_USER'))
    psync.add_argument(
        '--password', '-p',
        help=('Your O.G.R.E. password. '
              'You can also set the environment variable $EBOOK_PASS'))

    psync.add_argument(
        '--no-drm', action='store_true',
        help="Disable DRM removal during sync; don't install DeDRM tools")
    psync.add_argument(
        '--dry-run', '-d', action='store_true',
        help="Dry run the sync; don't actually upload anything to the server")


    # setup parser for stats command
    pstats = subparsers.add_parser('stats',
        parents=[parent_parser],
        help='View stats on your ebook library',
    )
    pstats.set_defaults(mode='stats')

    # set ogreserver params which apply to sync & stats
    for p in (psync, pstats):
        for provider, data in PROVIDERS.iteritems():
            if 'has_{}'.format(provider) in conf:
                p.add_argument(
                    '--ignore-{}'.format(provider), action='store_true',
                    help='Ignore ebooks in a local {} install'.format(data['friendly']))

        p.add_argument(
            '--ebook-home', '-H',
            help=('The directory where you keep your ebooks. '
                  'You can also set the environment variable $EBOOK_HOME'))


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


def main(conf, args, prntr):
    # setup config for sync
    conf.update({
        'debug': args.debug,
        'skip_cache': args.skip_cache,
        'verbose': True if args.debug is True else args.verbose,
        'quiet': args.quiet,
    })

    if args.mode == 'info':
        # display metadata from a single book
        ret = display_info(conf, prntr, args.inputfile)

    elif args.mode == 'dedrm':
        # decrypt a single book
        ret = dedrm_single_ebook(conf, prntr, args.inputfile, args.output_dir)

    elif args.mode == 'stats':
        # calculate and display library stats
        ret = stats(conf, prntr)

    elif args.mode == 'sync':
        # run ogreclient
        conf['no_drm'] = args.no_drm
        ret = run_sync(conf, prntr)

    return ret


def dedrm_single_ebook(conf, prntr, inputfile, output_dir):
    filename, ext = os.path.splitext(inputfile)
    from .dedrm import decrypt, DRM, DecryptionError

    try:
        prntr.p('Decrypting ebook {}'.format(os.path.basename(inputfile)), mode=prntr.DEDRM)

        state, decrypted_filepath = decrypt(
            inputfile, ext, conf['config_dir'], output_dir=output_dir
        )
        prntr.p('Book decrypted at:', extra=decrypted_filepath, success=True)

    except DecryptionError as e:
        prntr.p(str(e))
        state = None

    if state == DRM.decrypted:
        return 0
    else:
        return 1


def display_info(conf, prntr, filepath):
    ebook_obj = EbookObject(filepath)
    ebook_obj.get_metadata(conf)
    prntr.p('Book meta', extra=ebook_obj.meta)


def run_sync(conf, prntr):
    ret = False

    try:
        ret = sync(conf, prntr)

    # print messages on error
    except (AuthError, SyncError, UploadError) as e:
        prntr.e('Something went wrong.', excp=e)
    except AuthDeniedError:
        prntr.e('Permission denied. This is a private system.')
    except NoEbooksError:
        prntr.e('No ebooks found. Pass --ebook-home or set $EBOOK_HOME.')
    except Exception as e:
        prntr.e('Something went very wrong.', excp=e)

    return ret
