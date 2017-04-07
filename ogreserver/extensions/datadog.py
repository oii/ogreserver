from __future__ import absolute_import

import datadog


def init_datadog(app):
    '''
    DataDog integration setup
    '''
    datadog.initialize({
        'api_key': app.config.get('DATADOG_API_KEY'),
        'app_key': app.config.get('DATADOG_APP_KEY')
    })
