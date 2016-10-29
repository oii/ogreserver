import logging

import boto3
from flask import Flask, request
import requests


app = Flask(__name__)
logger = logging.getLogger('zappa')


@app.route('/', methods=['GET', 'POST'])
def forward():
    # retrieve EC2 instance name tag
    client = boto3.client('ec2', region_name='eu-west-1')
    data = client.describe_instances(
        Filters=[{'Name': 'instance-id', 'Values': [request.form.get('instance_id')]}]
    )['Reservations'][0]
    instance_name_tag = next((obj['Value'] for obj in data['Instances'][0]['Tags'] if obj['Key'] == 'Name'), None)

    logger.info(instance_name_tag)
    logger.info(request.form)

    # ping Slack
    resp = requests.post(
        'https://hooks.slack.com/services/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',
        json={
            'attachments': [{
                'title': '{} deployment'.format(instance_name_tag),
                'title_link': 'https://ogre.oii.yt/' if instance_name_tag == 'ogre-prod' else 'https://ogre-staging.oii.yt/',
                'fields': [{
                    'value': request.form.get('instance_id'),
                    'short': True
                }],
                'fallback': instance_name_tag,
                'color': 'good',
            }]
        }
    )
    return 'Slack says "{}"'.format(resp.text), resp.status_code
