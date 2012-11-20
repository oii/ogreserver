#! /usr/bin/env python

from argparse import ArgumentParser

from ogreclient import doit


def main():
    parser = ArgumentParser(description="O.G.R.E. client application")
    parser.add_argument(
        '--ebook-home', '-H', action="store", dest="ebook_home",
        help="The directory where you keep your ebooks")
    parser.add_argument(
        '--username', '-u', action="store", dest="username",
        help="Your O.G.R.E. username")
    parser.add_argument(
        '--password', '-p', action="store", dest="password",
        help="Your O.G.R.E. password")
    parser.add_argument(
        '--verbose', '-v', action="store_true", dest="verbose",
        help="Produce more output - this is just useful for debugging")
    parser.add_argument(
        '--quiet', '-q', action="store_true", dest="quiet",
        help="Don't produce any output")
    parser.add_argument(
        '--dry-run', '-d', action="store_true", dest="dry_run",
        help="Dry run the sync; don't actually upload anything to the server")

    args = parser.parse_args()

    doit(args.ebook_home, args.username, args.password)


if __name__ == "__main__":
    main()
