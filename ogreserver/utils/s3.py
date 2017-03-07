from __future__ import unicode_literals

import boto
import boto.s3
import boto.s3.connection


def connect_s3(config):
    """
    Connect to either AWS S3 or a local S3 proxy (for dev)
    """
    if config['DEBUG'] is True:
        # connect to s3proxy on 8880 in dev
        return boto.connect_s3(
            aws_access_key_id='identity',
            aws_secret_access_key='credential',
            host=config['VAGRANT_IP'],
            port=8880,
            is_secure=False,
            calling_format=boto.s3.connection.OrdinaryCallingFormat()
        )

    else:
        # connect to AWS
        return boto.s3.connect_to_region(
            config['AWS_REGION'],
            aws_access_key_id=config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=config['AWS_SECRET_ACCESS_KEY']
        )
