#!/usr/bin/env python

from __future__ import division
import urllib, urllib2
from urllib2 import HTTPError, URLError
import sys, os
from datetime import datetime

def doit():
    # setup the environment
    ebook_home = os.getenv("EBOOK_HOME")
    if ebook_home is None:
        print "You must set the $EBOOK_HOME environment variable"
        sys.exit(1)

    username = os.getenv("EBOOK_USER")
    if username is None:
        username = getpass.getuser()
        if username is not None:
            print "$EBOOK_USER is not set. Please enter your username, or press enter to use '%s':" % username
            ri = raw_input()
            if len(ri) > 0:
                username = ri

    if username is None:
        print "$EBOOK_USER is not set. Please enter your username, or press enter to exit:"
        username = raw_input()
        if len(username) == 0:
            sys.exit(1)

    password = os.getenv("EBOOK_PASS")
    if password is None:
        print "$EBOOK_PASS is not set. Please enter your password, or press enter to exit:"
        password = raw_input()
        if len(password) == 0:
            sys.exit(1)

    try:
        # authenticate the user, generating an api_key for subsequent requests
        #opener = urllib2.build_opener(urllib2.HTTPSHandler())
        #urllib2.install_opener(opener)
        params = urllib.urlencode({
            'username':username,
            'password':password
        })
        req = urllib2.Request(url='http://ogre.localhost/auth', data=params)
        f = urllib2.urlopen(req)
        api_key = f.read()

    except (HTTPError, URLError), e:
        print "Failed to connect: %s" % e
        sys.exit(1)

    print api_key


doit()

