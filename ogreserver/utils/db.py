from __future__ import unicode_literals

import datetime

import pytz


def date_to_rqltzinfo(data):
    '''
    Recursively convert datetime.date to datetime.datetime with UTC timezone
    '''
    def _convert(d):
        # reset time component to midnight and set UTC
        if type(d) is datetime.date:
            d = datetime.datetime.combine(d, datetime.time())
        return d.replace(tzinfo=pytz.UTC)

    # convert date or datetime immediately
    if type(data) is datetime.date or type(data) is datetime.datetime:
        return _convert(data)

    for k,v in data.items():
        if type(v) is dict:
            date_to_rqltzinfo(v)
        elif type(v) is datetime.date or type(v) is datetime.datetime:
            data[k] = _convert(v)


def rqltzinfo_to_iso8601(dt):
    if dt is None:
        return None
    return datetime.datetime.fromtimestamp(dt['epoch_time']).isoformat()
