import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


__all__ = ['strptime']


import datetime


def strptime(date_string):
    if not date_string:
        return None
    if date_string == '0001-01-01T00:00:00Z':
        return None
    return datetime.datetime.strptime(date_string[:26], '%Y-%m-%dT%H:%M:%S.%f')
