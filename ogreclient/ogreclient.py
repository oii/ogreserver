#!/usr/bin/env python

from __future__ import division
import urllib, urllib2
from urllib2 import HTTPError, URLError
import MultipartPostHandler
import sys, os, json, fnmatch, subprocess, getpass
from datetime import datetime
from utils import compute_md5

PROGBAR_LEN = 30

def doit():
    # setup the environment
    ebook_home = os.getenv("EBOOK_HOME")
    if ebook_home is None or len(ebook_home) == 0:
        print "You must set the $EBOOK_HOME environment variable"
        sys.exit(1)

    username = os.getenv("EBOOK_USER")
    if username is None or len(username) == 0:
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
    if password is None or len(password) == 0:
        print "$EBOOK_PASS is not set. Please enter your password, or press enter to exit:"
        password = getpass.getpass()
        if len(password) == 0:
            sys.exit(1)

    try:
        # authenticate the user, generating an api_key for subsequent requests
        params = urllib.urlencode({
            'username':username,
            'password':password
        })
        req = urllib2.Request(url='https://ogre.oii.me.uk/auth', data=params)
        f = urllib2.urlopen(req)
        api_key = f.read()

    except (HTTPError, URLError), e:
        print "Something went wrong.. Contact tha spodz: %s" % e
        sys.exit(1)

    ebooks = []
    output = []
    errors = []

    # a relatively quick search for all ebooks
    for root, dirs, files in os.walk(ebook_home):
        for filename in files:
            fn, ext = os.path.splitext(filename)
            if ext == ".epub" or ext == ".mobi" or ext == ".azw" or ext == ".pdf":
                filepath = os.path.join(root, filename)
                md5_tup = compute_md5(filepath)
                ebooks.append(
                    (filepath, fn, ext, md5_tup[2], md5_tup[0])
                )

    i = 0
    total = len(ebooks)
    if total == 0:
        print "No ebooks found. Is $EBOOK_HOME set correctly?"
        sys.exit(1)

    print "You have %s ebooks full of tasty meta. Nom nom.." % total
    ebooks_dict = {}

    # now parse all book meta data; building a complete dataset
    for item in ebooks:
        meta = subprocess.check_output(['ebook-meta', item[0]], stderr=subprocess.STDOUT)

        if meta.find("EPubException") > 0:
            # remove any corrupt
            errors.append(("Corrupt ebook",item[1]+item[2]))
        else:
            # parse author/title
            lines = meta.split("\n")
            for line in lines:
                if "Title" in line:
                    title = line[22:]

                if "Author" in line:
                    author = line[22:]
                    cut = author.find(" [")
                    if(cut > -1):
                        author = author[0:cut]

            # check for duplicates
            if author+" - "+title in ebooks_dict.keys() and item[2] in ebooks_dict[author+" - "+title].keys():
                # TODO warn user on error stack
                i = 0
            else:
                if author+" - "+title not in ebooks_dict.keys():
                    ebooks_dict[author+" - "+title] = {}

                # group books by meta data
                ebooks_dict[author+" - "+title][item[2]] = {
                    "path": item[0],
                    "filename": item[1],
                    "size": item[3],
                    "filehash": item[4],
                    "owner": username,
                }

        i += 1
        update_progress(i/total)

    sys.stdout.flush()
    print "\nCome on sucker, lick my battery"

    if len(errors) > 0:
        print "Some of this shit's fucked up, yo"
        print errors

    try:
        # post the json array of ebook data
        params = urllib.urlencode({
            'username':username,
            'api_key':api_key,
            'ebooks':json.dumps(ebooks_dict)
        })
        req = urllib2.Request(url='https://ogre.oii.me.uk/post', data=params)
        f = urllib2.urlopen(req)
        res = f.read()

        if res == "0":
            print "Something went wrong.. Contact tha spodz"
            sys.exit(1)

    except (HTTPError, URLError), e:
        print "Something went wrong.. Contact tha spodz: %s" % e
        sys.exit(1)

    # smash any relevant books upto the server
    response = json.loads(res)

    # uploading zero ebooks message
    if len(response['ebooks_to_upload']) == 0:
        for msg in response['messages']:
            print "%s %s" % msg

        return

    # grammatically correct messages are nice
    if len(response['ebooks_to_upload']) > 1:
        plural = "s"
    else:
        plural = ""

    print "Uploading %s ebook%s. Go make a brew." % (str(len(response['ebooks_to_upload'])), plural)

    # iterate all user's found books
    for authortitle in ebooks_dict.keys():
        for fmt in ebooks_dict[authortitle]:

            # upload each requested by the server
            for upload in response['ebooks_to_upload']:
                if upload['filehash'] == ebooks_dict[authortitle][fmt]['filehash']:
                    try:
                        f = open(ebooks_dict[authortitle][fmt]['path'], "rb")

                        # configure for uploads
                        opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler())
                        urllib2.install_opener(opener)

                        # build the post params
                        params = {
                            'username': username,
                            'api_key': api_key,
                            'sdbkey': upload['sdbkey'],
                            'filehash': upload['filehash'],
                            'ebook': f,
                        }
                        a = opener.open("https://ogre.oii.me.uk/upload", params)
                        msg = a.read()

                        upload['celery_task_id'] = msg

                    except (HTTPError, URLError), e:
                        print "Something went wrong.. Contact tha spodz: %s" % e
                        sys.exit(1)
                    except IOError, e:
                        continue
                    finally:
                        f.close()

    for msg in response['messages']:
        print "%s %s" % msg

    return


def update_progress(p):
    i = round(p*100, 1)
    sys.stdout.write("\r[{0}{1}] {2}%".format("#"*int(p*PROGBAR_LEN), " "*(PROGBAR_LEN-int(p*PROGBAR_LEN)), i))


doit()

