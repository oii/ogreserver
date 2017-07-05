Amazon Lambda Forwarder
=======================

A simple message forwarding app which uses AWS Lambda as a server-less backend.

- Forwards `cloud-init` phone-home notifications onto Slack - these occur when a new server starts

## Setup

Create a new virtualenv and install the contents of `requirements.txt`:

    virtualenv --python python2.7 . && source bin/activate
    pip install -r requirements.txt

## Deployment

The AWS side is managed with [zappa](https://github.com/Miserlou/Zappa):

    zappa deploy dev

And to update the existing app a simple:

    zappa update

## Debugging

Tail the AWS cloud watch logs for zappa apps with:

    zappa tail
