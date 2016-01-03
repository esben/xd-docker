"""Module containing helper functions for setting parameters on objects to be
passed on to requests calls."""

import logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


import re
from xd.docker.hostconfig import HostConfig


__all__ = ['set_integer', 'set_boolean', 'set_string', 'set_list_of_strings',
           'set_string_or_list_of_strings', 'set_dict_of_strings',
           'set_container_name', 'set_image_name',
           'set_hostname', 'set_domainname', 'set_user_name',
           'set_cpuset_list', 'set_list_of_ports',
           'set_host_config']


def set_integer(d, name, value, min=None, max=None):
    if value is None:
        return
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError('not integer value: %s' % type(value))
    if min is not None and value < min:
        raise ValueError('value too small: %d' % value)
    if max is not None and value > max:
        raise ValueError('value too big: %d' % value)
    d[name] = value


def set_boolean(d, name, value, ignore=[]):
    if value is None:
        return
    if not isinstance(value, bool):
        raise TypeError('not boolean value: %s' % type(value))
    if value in ignore:
        return
    d[name] = value


def set_string(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('value must be str: %s' % type(value))
    d[name] = value


def set_list_of_strings(d, name, value):
    if value is None:
        return
    if isinstance(value, list):
        for element in value:
            if not isinstance(element, str):
                raise ValueError('must be list of str')
    else:
        raise TypeError('must be list of str')
    d[name] = value


def set_string_or_list_of_strings(d, name, value):
    if value is None:
        return
    if isinstance(value, str):
        pass
    elif isinstance(value, list):
        for element in value:
            if not isinstance(element, str):
                raise ValueError('must be str or list of str')
    else:
        raise TypeError('must be str or list of str')
    d[name] = value


def set_dict_of_strings(d, name, value):
    if value is None:
        return
    if isinstance(value, dict):
        for key, element in value.items():
            if not isinstance(element, str):
                raise ValueError('must be dict of str')
    else:
        raise TypeError('must be dict of str')
    d[name] = value


CONTAINER_NAME_RE = re.compile(r'/?[a-zA-Z0-9_-]+$')


def set_container_name(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('container name must be str: %s' % type(value))
    if not CONTAINER_NAME_RE.match(value):
        raise ValueError('invalid container name: %s' % value)
    d[name] = value


REPOSITORY_NAME_RE = re.compile(r'[a-z0-9-_.]+$')


REPOSITORY_TAG_RE = re.compile(r'[a-zA-Z0-9-_.]+$')


IMAGE_NAME_RE = re.compile(r'%s(:%s)?$'%(
    REPOSITORY_NAME_RE.pattern[:-1], REPOSITORY_TAG_RE.pattern[:-1]))


def set_image_name(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('image_name must be str: %s' % type(value))
    if not IMAGE_NAME_RE.match(value):
        raise ValueError('invalid image name: %s' % value)
    d[name] = value


HOSTNAME_RE = re.compile(r'[a-z0-9]([a-z0-9-]*[a-z0-9])?$')


def set_hostname(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('hostname must be str: %s' % type(value))
    if not HOSTNAME_RE.match(value):
        raise ValueError('invalid hostname: %s' % value)
    d[name] = value


DOMAINNAME_RE = re.compile('%s(\.%s)*$' % (
    HOSTNAME_RE.pattern[:-1], HOSTNAME_RE.pattern[:-1]))


def set_domainname(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('domain name must be str: %s' % type(value))
    if not DOMAINNAME_RE.match(value):
        raise ValueError('invalid domain name: %s' % value)
    d[name] = value



USER_NAME_RE = re.compile(r'[a-z0-9][a-z0-9_-]*$')


def set_user_name(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('domain name must be str: %s' % type(value))
    if not USER_NAME_RE.match(value):
        raise ValueError('invalid user name: %s' % value)
    d[name] = value


CPUSET_LIST_RE = re.compile(r'(\d|[1-9]\d+)([,-](\d|[1-9]\d+))*$')


def set_cpuset_list(d, name, value):
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError('cpuset list value must be str: %s' % type(value))
    if not CPUSET_LIST_RE.match(value):
        raise ValueError('invalid cpuset list: %s' % value)
    d[name] = value


PORT_RE = re.compile(r'[1-9]\d*/(tcp|udp)$')


def set_list_of_ports(d, name, value):
    if value is None:
        return
    if not isinstance(value, list):
        raise TypeError('value must be list of str: %s' % type(value))
    for element in value:
        if not isinstance(element, str):
            raise TypeError('value must be list of str: %s' % type(value))
        if not PORT_RE.match(element):
            raise ValueError('invalid port specification: %s' % (element))
    d[name] = value


def set_host_config(d, name, value, api_version):
    if value is None:
        return
    if not isinstance(value, HostConfig):
        raise TypeError('value must be HostConfig: %s' % type(value))
    d[name] = value.json_object(api_version)
