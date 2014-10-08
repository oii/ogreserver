from __future__ import absolute_import

import argparse
import os
import sys

from . import __version__

from .core import sync, metadata_extract
from .dedrm import download_dedrm
from .prereqs import setup_ogreclient
from .printer import CliPrinter, DummyPrinter

from .exceptions import OgreException, ConfigSetupError
from .exceptions import AuthDeniedError, AuthError, NoEbooksError, NoUploadsError
from .exceptions import BaconError, MushroomError, SpinachError


def entrypoint():
    ret = False
    prntr = None

    try:
        # setup and run argparse
        args = parse_command_line()

        # global CLI printer
        if args.quiet is True:
            prntr = DummyPrinter()
        else:
            prntr = CliPrinter(debug=args.debug)

            # set printer to log everything for later dispatch to ogreserver
            if args.debug is True:
                prntr.log_output = True

        # run some checks and create some config variables
        conf = setup_ogreclient(args, prntr)

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
        help='Print debug information on error & pass to ogreserver, also ignore local cache')
    psync.add_argument(
        '--use-cache', action='store_true',
        help='Used in conjunction with --debug to allow debugging of caching code paths')
    psync.add_argument(
        '--quiet', '-q', action='store_true',
        help="Don't produce any output")
    psync.add_argument(
        '--dry-run', '-d', action='store_true',
        help="Dry run the sync; don't actually upload anything to the server")

    psync.add_argument(
        '--ignore-kindle', action='store_true',
        help='Ignore ebooks in a local Amazon Kindle install')

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


def main(conf, args, prntr):
    # setup config for sync
    conf.update({
        'debug': args.debug,
        'use_cache': args.use_cache,
        'verbose': True if args.debug is True else args.verbose,
        'quiet': args.quiet,
    })

    if args.mode == 'update':
        ret = download_dedrm(args.host, conf['username'], conf['password'], prntr, debug=args.debug)

    elif args.mode == 'info':
        # display metadata from a single book
        ret = display_info(conf, prntr, args.inputfile)

    elif args.mode == 'dedrm':
        # decrypt a single book
        ret = dedrm_single_ebook(conf, prntr, args.inputfile, args.output_dir)

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
    meta = metadata_extract(conf['calibre_ebook_meta_bin'], filepath)
    prntr.p('Book meta', extra=meta)


def run_sync(conf, prntr):
    ret = False

    try:
        ret = sync(conf, prntr)

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
        prntr.e('Something went very wrong.', excp=e)

    return ret
