import unittest
import pytest
import ipaddress

from xd.docker.parameters import *


class parameter_tests(unittest.case.TestCase):

    def test_notimplemented(self):
        p = Parameter()
        with pytest.raises(NotImplementedError):
            p.json()


class env_tests(unittest.case.TestCase):

    def test_no_arg(self):
        env = Env()
        self.assertIsNone(env.json())

    def test_empty_arg(self):
        env = Env({})
        self.assertEqual(env.json(), [])

    def test_string_value(self):
        env = Env({'foo': 'bar'})
        self.assertEqual(env.json(), ['foo=bar'])

    def test_int_value(self):
        env = Env({'foo': 42})
        self.assertEqual(env.json(), ['foo=42'])

    def test_int_string(self):
        env = Env({'foo': '42'})
        self.assertEqual(env.json(), ['foo=42'])

    def test_int_key(self):
        with pytest.raises(TypeError):
            env = Env({43: 42})

    def test_bad_key_1(self):
        with pytest.raises(ValueError):
            env = Env({',foo': 'bar'})

    def test_bad_key_2(self):
        with pytest.raises(ValueError):
            env = Env({'foo=': 'bar'})

    def test_bad_key_3(self):
        with pytest.raises(ValueError):
            env = Env({'0foo': 'bar'})

    def test_multiple_2(self):
        env = Env({'foo': 'hello', 'bar': 'world'})
        self.assertEqual(sorted(env.json()),
                         sorted(['foo=hello', 'bar=world']))

    def test_multiple_4(self):
        env = Env({'foo': 'hello', 'bar': 'world', 'x': 42, 'y': 43})
        self.assertEqual(sorted(env.json()),
                         sorted(['foo=hello', 'bar=world','x=42', 'y=43']))

    def test_str(self):
        env = Env({'foo': 'bar'})
        self.assertEqual(str(env), "['foo=bar']")


class port_tests(unittest.case.TestCase):

    def test_42(self):
        port = Port(42)
        self.assertEqual(port.json(), '42/tcp')

    def test_0(self):
        with pytest.raises(ValueError):
            Port(0)

    def test_minus_1(self):
        with pytest.raises(ValueError):
            Port(-1)

    def test_65535(self):
        port = Port(65535)
        self.assertEqual(port.json(), '65535/tcp')

    def test_65536(self):
        with pytest.raises(ValueError):
            Port(65536)

    def test_42_tcp(self):
        port = Port(42, 'tcp')
        self.assertEqual(port.json(), '42/tcp')

    def test_42_udp(self):
        port = Port(42, 'udp')
        self.assertEqual(port.json(), '42/udp')

    def test_42_foo(self):
        with pytest.raises(ValueError):
            Port(42, 'foo')


class portbinding_tests(unittest.case.TestCase):

    def test_42(self):
        port = PortBinding(42)
        self.assertEqual(port.json(), {'42/tcp': [{'HostPort': '42'}]})

    def test_0(self):
        with pytest.raises(ValueError):
            PortBinding(0)

    def test_minus_1(self):
        with pytest.raises(ValueError):
            PortBinding(-1)

    def test_65535(self):
        port = PortBinding(65535)
        self.assertEqual(port.json(),
                         {'65535/tcp': [{'HostPort': '65535'}]})

    def test_65536(self):
        with pytest.raises(ValueError):
            PortBinding(65536)

    def test_42_tcp(self):
        port = PortBinding(42, 'tcp')
        self.assertEqual(port.json(), {'42/tcp': [{'HostPort': '42'}]})

    def test_42_udp(self):
        port = PortBinding(42, 'udp')
        self.assertEqual(port.json(), {'42/udp': [{'HostPort': '42'}]})

    def test_42_foo(self):
        with pytest.raises(ValueError):
            PortBinding(42, 'foo')

    def test_hostport_43(self):
        port = PortBinding(42, host_port=43)
        self.assertEqual(port.json(), {'42/tcp': [{'HostPort': '43'}]})

    def test_hostport_1(self):
        port = PortBinding(42, host_port=1)
        self.assertEqual(port.json(), {'42/tcp': [{'HostPort': '1'}]})

    def test_hostport_0(self):
        with pytest.raises(ValueError):
            PortBinding(42, host_port=0)

    def test_hostport_minus_1(self):
        with pytest.raises(ValueError):
            PortBinding(42, host_port=-1)

    def test_hostport_65535(self):
        port = PortBinding(42, host_port=65535)
        self.assertEqual(port.json(), {'42/tcp':
                                              [{'HostPort': '65535'}]})

    def test_hostport_65536(self):
        with pytest.raises(ValueError):
            PortBinding(42, host_port=65536)

    def test_host_ip(self):
        port = PortBinding(42, host_ip='192.168.1.1')
        self.assertEqual(port.json(),
                         {'42/tcp': [{'HostPort': '42',
                                      'HostIp': '192.168.1.1'}]})


class volumemount_tests(unittest.case.TestCase):

    def test_default(self):
        vm = VolumeMount('/foo', '/bar')
        assert vm.json() == {'Source': '/foo', 'Destination': '/bar',
                             'RW': True, 'Mode': 'rw'}

    def test_ro(self):
        vm = VolumeMount('/foo', '/bar', ro=True)
        assert vm.json() == {'Source': '/foo', 'Destination': '/bar',
                             'RW': False, 'Mode': 'ro'}

    def test_z(self):
        vm = VolumeMount('/foo', '/bar', label_mode='z')
        assert vm.json() == {'Source': '/foo', 'Destination': '/bar',
                             'RW': True, 'Mode': 'rw,z'}

    def test_Z(self):
        vm = VolumeMount('/foo', '/bar', label_mode='Z')
        assert vm.json() == {'Source': '/foo', 'Destination': '/bar',
                             'RW': True, 'Mode': 'rw,Z'}


class volumebinding_tests(unittest.case.TestCase):

    def test_default(self):
        vb = VolumeBinding('/foo')
        assert vb.json() == '/foo'

    def test_host_path(self):
        vb = VolumeBinding('/foo', '/bar')
        assert vb.json() == '/bar:/foo'

    def test_ro(self):
        vb = VolumeBinding('/foo', '/bar', ro=True)
        assert vb.json() == '/bar:/foo:ro'

    def test_invalid_container_path(self):
        with pytest.raises(ValueError):
            VolumeBinding('')

    def test_invalid_host_path(self):
        with pytest.raises(ValueError):
            VolumeBinding('/foo', '')

    def test_ro_and_no_host_path(self):
        with pytest.raises(ValueError):
            VolumeBinding('/foo', ro=True)


class containerlink_tests(unittest.case.TestCase):

    def test_default(self):
        cl = ContainerLink('foo', 'bar')
        assert cl.json() == 'foo:bar'


class cpuset_tests(unittest.case.TestCase):

    def test_single_digit_0(self):
        cs = Cpuset('0')
        assert cs.json() == '0'

    def test_single_digit_1(self):
        cs = Cpuset('1')
        assert cs.json() == '1'

    def test_single_digit_9(self):
        cs = Cpuset('9')
        assert cs.json() == '9'

    def test_double_digit_42(self):
        cs = Cpuset('42')
        assert cs.json() == '42'

    def test_double_digit_09(self):
        with pytest.raises(ValueError):
            cs = Cpuset('09')

    def test_many_digits_1234(self):
        cs = Cpuset('1234')
        assert cs.json() == '1234'

    def test_two_numbers_42_43(self):
        cs = Cpuset('42,43')
        assert cs.json() == '42,43'

    def test_two_numbers_42_09(self):
        with pytest.raises(ValueError):
            cs = Cpuset('42,09')

    def test_four_numbers(self):
        cs = Cpuset('42,43,1024,147')
        assert cs.json() == '42,43,1024,147'

    def test_range(self):
        cs = Cpuset('0-4')
        assert cs.json() == '0-4'

    def test_range_and_numbers_1(self):
        cs = Cpuset('0-4,7')
        assert cs.json() == '0-4,7'

    def test_range_and_numbers_2(self):
        cs = Cpuset('0,4-7')
        assert cs.json() == '0,4-7'

    def test_starting_with_comma(self):
        with pytest.raises(ValueError):
            cs = Cpuset(',42')

    def test_ending_with_comma(self):
        with pytest.raises(ValueError):
            cs = Cpuset('42,')

    def test_word(self):
        with pytest.raises(ValueError):
            cs = Cpuset('bar')

    def test_name_with_caps(self):
        with pytest.raises(ValueError):
            cs = Cpuset('BAR')

    def test_name_with_number(self):
        with pytest.raises(ValueError):
            cs = Cpuset('foo2bar')

    def test_name_starting_with_number(self):
        with pytest.raises(ValueError):
            cs = Cpuset('2bar')

    def test_number_and_semicolon(self):
        with pytest.raises(ValueError):
            cs = Cpuset('42;43')

    def test_number_and_hash(self):
        with pytest.raises(ValueError):
            cs = Cpuset('42#43')

    def test_number_and_dollar(self):
        with pytest.raises(ValueError):
            cs = Cpuset('42$43')

    def test_empty_string(self):
        with pytest.raises(ValueError):
            cs = Cpuset('')

    def test_none(self):
        with pytest.raises(TypeError):
            Cpuset(None)

    def test_int(self):
        with pytest.raises(TypeError):
            cs = Cpuset(42)

    def test_list(self):
        with pytest.raises(TypeError):
            cs = Cpuset(['42'])

    def test_dict(self):
        with pytest.raises(TypeError):
            cs = Cpuset({'bar': '42'})

    def test_boolean(self):
        with pytest.raises(TypeError):
            cs = Cpuset(True)


class hostname_tests(unittest.case.TestCase):

    def test_name(self):
        hn = Hostname('bar')
        assert hn.json() == 'bar'

    def test_name_with_caps(self):
        with pytest.raises(ValueError):
            Hostname('BAR')

    def test_name_with_number(self):
        hn = Hostname('foo2bar')
        assert hn.json() == 'foo2bar'

    def test_name_starting_with_number(self):
        hn = Hostname('2bar')
        assert hn.json() == '2bar'

    def test_name_with_underscore(self):
        with pytest.raises(ValueError):
            Hostname('foo_bar')

    def test_name_with_dash(self):
        hn = Hostname('foo-bar')
        assert hn.json() == 'foo-bar'

    def test_name_starting_with_dash(self):
        with pytest.raises(ValueError):
            Hostname('-bar')

    def test_name_with_dot(self):
        with pytest.raises(ValueError):
            Hostname('foo.bar')

    def test_empty_string(self):
        with pytest.raises(ValueError):
            Hostname('')

    def test_none(self):
        with pytest.raises(TypeError):
            Hostname(None)

    def test_int(self):
        with pytest.raises(TypeError):
            Hostname(42)

    def test_list(self):
        with pytest.raises(TypeError):
            Hostname(['bar'])

    def test_dict(self):
        with pytest.raises(TypeError):
            Hostname({'bar': 'foobar'})

    def test_boolean(self):
        with pytest.raises(TypeError):
            Hostname(True)


class domainname_tests(unittest.case.TestCase):

    def test_name(self):
        dn = Domainname('bar')
        assert dn.json() == 'bar'

    def test_name_with_caps(self):
        with pytest.raises(ValueError):
            Domainname('BAR')

    def test_name_with_number(self):
        dn = Domainname('foo2bar')
        assert dn.json() == 'foo2bar'

    def test_name_starting_with_number(self):
        dn = Domainname('2bar')
        assert dn.json() == '2bar'

    def test_name_with_underscore(self):
        with pytest.raises(ValueError):
            Domainname('foo_bar')

    def test_name_with_dash(self):
        dn = Domainname('foo-bar')
        assert dn.json() == 'foo-bar'

    def test_name_starting_with_dash(self):
        with pytest.raises(ValueError):
            Domainname('-bar')

    def test_name_with_dot(self):
        dn = Domainname('foo.bar')
        assert dn.json() == 'foo.bar'

    def test_empty_string(self):
        with pytest.raises(ValueError):
            Domainname('')

    def test_none(self):
        with pytest.raises(TypeError):
            Domainname(None)

    def test_int(self):
        with pytest.raises(TypeError):
            Domainname(42)

    def test_list(self):
        with pytest.raises(TypeError):
            Domainname(['bar'])

    def test_dict(self):
        with pytest.raises(TypeError):
            Domainname({'bar': 'foobar'})

    def test_boolean(self):
        with pytest.raises(TypeError):
            Domainname(True)


class macaddress_tests(unittest.case.TestCase):

    def test_valid_1(self):
        addr = MacAddress('01:23:45:67:89:01')
        assert addr.json() == '01:23:45:67:89:01'

    def test_valid_2(self):
        addr = MacAddress('ab:cd:ef:ab:89:01')
        assert addr.json() == 'ab:cd:ef:ab:89:01'

    def test_valid_3(self):
        addr = MacAddress('01:AB:CD:EF:89:01')
        assert addr.json() == '01:AB:CD:EF:89:01'

    def test_invalid_1(self):
        with pytest.raises(ValueError):
            MacAddress('foo')

    def test_invalid_2(self):
        with pytest.raises(ValueError):
            MacAddress('01')

    def test_invalid_3(self):
        with pytest.raises(ValueError):
            MacAddress('01:23:45:67:89:0')

    def test_invalid_4(self):
        with pytest.raises(ValueError):
            MacAddress('01:23:45:67:89:0g')

    def test_invalid_5(self):
        with pytest.raises(ValueError):
            MacAddress('01:23:45:67:89:0G')

    def test_invalid_6(self):
        with pytest.raises(ValueError):
            MacAddress('g1:23:45:67:89:01')

    def test_invalid_7(self):
        with pytest.raises(ValueError):
            MacAddress('G1:23:45:67:89:01')


class username_tests(unittest.case.TestCase):

    def test_name(self):
        user = Username('bar')
        assert user.json() == 'bar'

    def test_name_with_caps(self):
        with pytest.raises(ValueError):
            Username('BAR')

    def test_name_with_number(self):
        user = Username('foo2bar')
        assert user.json() == 'foo2bar'

    def test_name_starting_with_number(self):
        user = Username('2bar')
        assert user.json() == '2bar'

    def test_name_with_underscore(self):
        user = Username('foo_bar')
        assert user.json() == 'foo_bar'

    def test_name_starting_with_underscore(self):
        with pytest.raises(ValueError):
            Username('_bar')

    def test_name_with_dash(self):
        user = Username('foo-bar')
        assert user.json() == 'foo-bar'

    def test_name_starting_with_dash(self):
        with pytest.raises(ValueError):
            Username('-bar')

    def test_name_with_dot(self):
        with pytest.raises(ValueError):
            Username('foo.bar')

    def test_name_with_semicolon(self):
        with pytest.raises(ValueError):
            Username('foo;bar')

    def test_name_with_hash(self):
        with pytest.raises(ValueError):
            Username('foo#bar')

    def test_name_with_dollar(self):
        with pytest.raises(ValueError):
            Username('foo$bar')

    def test_empty_string(self):
        with pytest.raises(ValueError):
            Username('')

    def test_none(self):
        with pytest.raises(TypeError):
            Username(None)

    def test_int(self):
        with pytest.raises(TypeError):
            Username(42)

    def test_list(self):
        with pytest.raises(TypeError):
            Username(['bar'])

    def test_dict(self):
        with pytest.raises(TypeError):
            Username({'bar': 'foobar'})

    def test_boolean(self):
        with pytest.raises(TypeError):
            Username(True)


class hostnameipmapping_tests(unittest.case.TestCase):

    def test_str_hostname(self):
        him = HostnameIPMapping('foo', '192.168.0.1')
        assert him.json() == 'foo:192.168.0.1'

    def test_str_domainname(self):
        him = HostnameIPMapping('foo.bar', '192.168.0.1')
        assert him.json() == 'foo.bar:192.168.0.1'

    def test_hostname(self):
        him = HostnameIPMapping(Hostname('foo'), '192.168.0.1')
        assert him.json() == 'foo:192.168.0.1'

    def test_domainname(self):
        him = HostnameIPMapping(Domainname('foo.bar'), '192.168.0.1')
        assert him.json() == 'foo.bar:192.168.0.1'

    def test_str_ipv4(self):
        him = HostnameIPMapping('foo', '192.168.0.1')
        assert him.json() == 'foo:192.168.0.1'

    def test_str_ipv6(self):
        him = HostnameIPMapping('foo', '2001:db8::1')
        assert him.json() == 'foo:2001:db8::1'

    def test_ipv4(self):
        him = HostnameIPMapping('foo', ipaddress.IPv4Address('192.168.0.1'))
        assert him.json() == 'foo:192.168.0.1'

    def test_ipv6(self):
        him = HostnameIPMapping('foo', ipaddress.IPv6Address('2001:db8::1'))
        assert him.json() == 'foo:2001:db8::1'

    def test_invalid_ip(self):
        with pytest.raises(ValueError):
            HostnameIPMapping('foo', 'bar')


class volumesfrom_tests(unittest.case.TestCase):

    def test_default(self):
        vf = VolumesFrom('foo')
        assert vf.json() == 'foo'

    def test_ro(self):
        vf = VolumesFrom('foo', ro=True)
        assert vf.json() == 'foo:ro'

    def test_rw(self):
        vf = VolumesFrom('foo', ro=False)
        assert vf.json() == 'foo:rw'


class restartpolicy_tests(unittest.case.TestCase):

    def test_always(self):
        rp = RestartPolicy('always')
        assert rp.json() == {'Name': 'always'}

    def test_unless_stopped(self):
        rp = RestartPolicy('unless-stopped')
        assert rp.json() == {'Name': 'unless-stopped'}

    def test_on_failure_42(self):
        rp = RestartPolicy('on-failure', 42)
        assert rp.json() == {'Name': 'on-failure', 'MaximumRetryCount': 42}

    def test_on_failure_0(self):
        rp = RestartPolicy('on-failure', 0)
        assert rp.json() == {'Name': 'on-failure', 'MaximumRetryCount': 0}

    def test_on_failure_no_arg(self):
        with pytest.raises(TypeError):
            RestartPolicy('on-failure')

    def test_on_failure_negative(self):
        with pytest.raises(ValueError):
            RestartPolicy('on-failure', -1)


class devicetoadd_tests(unittest.case.TestCase):

    def test_1_arg(self):
        dta = DeviceToAdd('/foo')
        assert dta.json() == {'PathOnHost': '/foo',
                              'PathInContainer': '/foo',
                              'CgroupPermissions': 'rwm'}

    def test_2_args(self):
        dta = DeviceToAdd('/foo', '/bar')
        assert dta.json() == {'PathOnHost': '/foo',
                              'PathInContainer': '/bar',
                              'CgroupPermissions': 'rwm'}

    def test_cgroup(self):
        dta = DeviceToAdd('/foo', cgroup_permissions='rw')
        assert dta.json() == {'PathOnHost': '/foo',
                              'PathInContainer': '/foo',
                              'CgroupPermissions': 'rw'}


class ulimit_tests(unittest.case.TestCase):

    def test_default(self):
        ul = Ulimit('nofile', 1024)
        assert ul.json() == {'Name': 'nofile',
                              'Soft': 1024,
                              'Hard': 1024}

    def test_hard(self):
        ul = Ulimit('nofile', 1024, 4096)
        assert ul.json() == {'Name': 'nofile',
                              'Soft': 1024,
                              'Hard': 4096}


class logconfiguration_tests(unittest.case.TestCase):

    def test_default(self):
        lc = LogConfiguration('json-file')
        assert lc.json() == {'Type': 'json-file', 'Config': None}

    def test_empty_config(self):
        lc = LogConfiguration('json-file', {})
        assert lc.json() == {'Type': 'json-file', 'Config': {}}

    def test_invalid_type(self):
        with pytest.raises(ValueError):
            LogConfiguration('foobar')


class authconfig_tests(unittest.case.TestCase):

    def test_credential_without_email(self):
        ac = CredentialAuthConfig('me', 'secret')
        assert ac.json() == {'username': 'me', 'password': 'secret'}

    def test_credential_with_email(self):
        ac = CredentialAuthConfig('me', 'secret', 'me@domain.com')
        assert ac.json() == {'username': 'me', 'password': 'secret',
                             'email': 'me@domain.com'}

    def test_token(self):
        ac = TokenAuthConfig('foobar')
        assert ac.json() == {'registrytoken': 'foobar'}


class registryauthconfig_tests(unittest.case.TestCase):

    def test_empty(self):
        rac = RegistryAuthConfig([])
        assert rac.json() == {}

    def test_1_cred(self):
        rac = RegistryAuthConfig({'https://index.docker.io/v1/':
                                  CredentialAuthConfig('me', 'secret')})
        assert rac.json() == {'https://index.docker.io/v1/': {
            'username': 'me', 'password': 'secret'}}

    def test_2_cred(self):
        rac = RegistryAuthConfig({'https://index.docker.io/v1/':
                                  CredentialAuthConfig('me', 'secret'),
                                  'docker.example.com':
                                  CredentialAuthConfig('you', 'public')})
        assert rac.json() == {
            'https://index.docker.io/v1/': {
                'username': 'me', 'password': 'secret'},
            'docker.example.com': {'username': 'you', 'password': 'public'}}

    def test_1_token(self):
        rac = RegistryAuthConfig({
            'https://index.docker.io/v1/': TokenAuthConfig('foobar')})
        assert rac.json() == {'https://index.docker.io/v1/': {
            'registrytoken': 'foobar'}}


class repository_tests(unittest.case.TestCase):

    def test_name(self):
        tag = Repository('foo')
        assert tag.json() == 'foo'

    def test_name_and_tag(self):
        tag = Repository('foo:bar')
        assert tag.json() == 'foo:bar'

    def test_empty(self):
        with pytest.raises(ValueError):
            Repository('')

    def test_invalid_1(self):
        with pytest.raises(ValueError):
            Repository('foo:bar:x')


class repotags_tests(unittest.case.TestCase):

    def test_no_tags(self):
        repo_tags = RepoTags([])
        assert repo_tags.repos == []
        assert repo_tags.json() == []

    def test_1(self):
        repo_tags = RepoTags(['busybox:latest'])
        assert len(repo_tags.repos) == 1
        assert isinstance(repo_tags.repos[0], Repository)
        assert repo_tags.repos[0].name == 'busybox'
        assert repo_tags.repos[0].tag == 'latest'
        assert repo_tags.json() == ['busybox:latest']

    def test_2(self):
        repo_tags = RepoTags(['busybox:latest', 'foo:bar'])
        assert len(repo_tags.repos) == 2
        for repo in repo_tags.repos:
            assert isinstance(repo, Repository)


class containername_tests(unittest.case.TestCase):

    def test_name(self):
        c = ContainerName('foo')
        assert c.json() == 'foo'

    def test_caps(self):
        c = ContainerName('FOO')
        assert c.json() == 'FOO'

    def test_name_with_number(self):
        c = ContainerName('foo42')
        assert c.json() == 'foo42'

    def test_name_with_underscore(self):
        c = ContainerName('foo_bar')
        assert c.json() == 'foo_bar'

    def test_name_with_dash(self):
        c = ContainerName('foo-bar')
        assert c.json() == 'foo-bar'

    def test_empty(self):
        with pytest.raises(ValueError):
            ContainerName('')


class containerconfig_tests(unittest.case.TestCase):

    def test_default(self):
        cc = ContainerConfig('foo')
        assert cc.json() == {'Image': 'foo'}

    def test_command_str(self):
        cc = ContainerConfig('foo', command='echo foo')
        assert cc.json() == {'Image': 'foo',
                             'Cmd': 'echo foo'}

    def test_command_array(self):
        cc = ContainerConfig('foo', command=['echo', 'foo'])
        assert cc.json() == {'Image': 'foo',
                             'Cmd': ['echo', 'foo']}

    def test_entrypoint_str(self):
        cc = ContainerConfig('foo', entrypoint='echo foo')
        assert cc.json(api_version=(1, 15)) == {'Image': 'foo',
                                                'Entrypoint': 'echo foo'}

    def test_entrypoint_array(self):
        cc = ContainerConfig('foo', entrypoint=['echo', 'foo'])
        assert cc.json(api_version=(1, 15)) == {'Image': 'foo',
                             'Entrypoint': ['echo', 'foo']}

    def test_entrypoint_not_supported(self):
        cc = ContainerConfig('foo', entrypoint='echo foo')
        with pytest.raises(ValueError):
            cc.json(api_version=(1, 14))

    def test_on_build(self):
        cc = ContainerConfig('foo', on_build=['echo', 'foo'])
        assert cc.json(api_version=(1, 16)) == {'Image': 'foo',
                                                'OnBuild': ['echo', 'foo']}

    def test_on_build(self):
        cc = ContainerConfig('foo', on_build=['echo', 'foo'])
        with pytest.raises(ValueError):
            cc.json(api_version=(1, 15))

    def test_hostname(self):
        cc = ContainerConfig('foo', hostname=Hostname('bar'))
        assert cc.json() == {'Image': 'foo', 'Hostname': 'bar'}

    def test_hostname_str(self):
        cc = ContainerConfig('foo', hostname='bar')
        assert cc.json() == {'Image': 'foo', 'Hostname': 'bar'}

    def test_hostname_domainname(self):
        with pytest.raises(TypeError):
            ContainerConfig('foo', hostname=Domainname('bar'))

    def test_domainname(self):
        cc = ContainerConfig('foo', domainname=Domainname('foo.bar'))
        assert cc.json() == {'Image': 'foo', 'Domainname': 'foo.bar'}

    def test_domainname_str(self):
        cc = ContainerConfig('foo', domainname='foo.bar')
        assert cc.json() == {'Image': 'foo', 'Domainname': 'foo.bar'}

    def test_user(self):
        cc = ContainerConfig('foo', user=Username('me'))
        assert cc.json() == {'Image': 'foo', 'User': 'me'}

    def test_user_str(self):
        cc = ContainerConfig('foo', user='me')
        assert cc.json() == {'Image': 'foo', 'User': 'me'}

    def test_user_invalid(self):
        with pytest.raises(ValueError):
            ContainerConfig('foo', user='-')

    def test_attach_stdin_true(self):
        cc = ContainerConfig('foo', attach_stdin=True)
        assert cc.json() == {'Image': 'foo', 'AttachStdin': True}

    def test_attach_stdin_false(self):
        cc = ContainerConfig('foo', attach_stdin=False)
        assert cc.json() == {'Image': 'foo', 'AttachStdin': False}

    def test_attach_stdout_true(self):
        cc = ContainerConfig('foo', attach_stdout=True)
        assert cc.json() == {'Image': 'foo', 'AttachStdout': True}

    def test_attach_stdout_false(self):
        cc = ContainerConfig('foo', attach_stdout=False)
        assert cc.json() == {'Image': 'foo', 'AttachStdout': False}

    def test_attach_stderr_true(self):
        cc = ContainerConfig('foo', attach_stderr=True)
        assert cc.json() == {'Image': 'foo', 'AttachStderr': True}

    def test_attach_stderr_false(self):
        cc = ContainerConfig('foo', attach_stderr=False)
        assert cc.json() == {'Image': 'foo', 'AttachStderr': False}

    def test_attach_tty_true(self):
        cc = ContainerConfig('foo', tty=True)
        assert cc.json() == {'Image': 'foo', 'Tty': True}

    def test_attach_tty_false(self):
        cc = ContainerConfig('foo', tty=False)
        assert cc.json() == {'Image': 'foo', 'Tty': False}

    def test_attach_open_stdin_true(self):
        cc = ContainerConfig('foo', open_stdin=True)
        assert cc.json() == {'Image': 'foo', 'OpenStdin': True}

    def test_attach_open_stdin_false(self):
        cc = ContainerConfig('foo', open_stdin=False)
        assert cc.json() == {'Image': 'foo', 'OpenStdin': False}

    def test_attach_stdin_once_true(self):
        cc = ContainerConfig('foo', stdin_once=True)
        assert cc.json() == {'Image': 'foo', 'StdinOnce': True}

    def test_attach_stdin_once_false(self):
        cc = ContainerConfig('foo', stdin_once=False)
        assert cc.json() == {'Image': 'foo', 'StdinOnce': False}

    def test_env(self):
        cc = ContainerConfig('foo', env=Env({'hello': 'world'}))
        assert cc.json() == {'Image': 'foo', 'Env': ['hello=world']}

    def test_env_none(self):
        e = Env()
        print('e in test:', e)
        cc = ContainerConfig('foo', env=Env())
        assert cc.json() == {'Image': 'foo'}

    def test_env_empty(self):
        cc = ContainerConfig('foo', env=Env({}))
        assert cc.json() == {'Image': 'foo', 'Env': []}

    def test_env_dict(self):
        cc = ContainerConfig('foo', env={'hello': 'world'})
        assert cc.json() == {'Image': 'foo', 'Env': ['hello=world']}

    def test_env_dict_empty(self):
        cc = ContainerConfig('foo', env={})
        assert cc.json() == {'Image': 'foo', 'Env': []}

    def test_labels(self):
        cc = ContainerConfig('foo', labels={'hello': 'world'})
        assert cc.json(api_version=(1, 18)) == {
            'Image': 'foo', 'Labels': {'hello': 'world'}}

    def test_labels_not_supported(self):
        cc = ContainerConfig('foo', labels={'hello': 'world'})
        with pytest.raises(ValueError):
            cc.json(api_version=(1, 17))

    def test_working_dir(self):
        cc = ContainerConfig('foo', working_dir='/foo')
        assert cc.json() == {'Image': 'foo', 'WorkingDir': '/foo'}

    def test_network_default(self):
        cc = ContainerConfig('foo')
        assert cc.json() == {'Image': 'foo'}

    def test_network_true(self):
        cc = ContainerConfig('foo', network=True)
        assert cc.json() == {'Image': 'foo', 'NetworkDisabled': False}

    def test_network_false(self):
        cc = ContainerConfig('foo', network=False)
        assert cc.json() == {'Image': 'foo', 'NetworkDisabled': True}

    def test_mac_address(self):
        cc = ContainerConfig(
            'foo', mac_address=MacAddress('01:23:45:ab:cd:ef'))
        assert cc.json(api_version=(1, 15)) == {
            'Image': 'foo', 'MacAddress': '01:23:45:ab:cd:ef'}

    def test_mac_address_str(self):
        cc = ContainerConfig('foo', mac_address='01:23:45:ab:cd:ef')
        assert cc.json(api_version=(1, 15)) == {
            'Image': 'foo', 'MacAddress': '01:23:45:ab:cd:ef'}

    def test_mac_address_invalid(self):
        with pytest.raises(ValueError):
            ContainerConfig('foo', mac_address='42')

    def test_mac_address_unsupported(self):
        cc = ContainerConfig(
            'foo', mac_address=MacAddress('01:23:45:ab:cd:ef'))
        with pytest.raises(ValueError):
            cc.json(api_version=(1, 14))

    def test_volumes_1(self):
        cc = ContainerConfig('foo', volumes=['/foo'])
        assert cc.json() == {'Image': 'foo',
                             'Volumes': {'/foo': {}}}

    def test_volumes_2(self):
        cc = ContainerConfig('foo', volumes=['/foo', '/bar'])
        assert cc.json() == {'Image': 'foo',
                             'Volumes': {'/foo': {}, '/bar': {}}}


class hostconfig_tests(unittest.case.TestCase):

    def test_default(self):
        hc = HostConfig()
        assert hc.json() == {}

    def test_binds(self):
        hc = HostConfig(binds=[VolumeBinding('/container', '/host')])
        assert hc.json() == {'Binds': ['/host:/container']}

    def test_binds_empty(self):
        hc = HostConfig(binds=[])
        assert hc.json() == {'Binds': []}

    def test_links(self):
        hc = HostConfig(links=[ContainerLink('foo', 'bar')])
        assert hc.json() == {'Links': ['foo:bar']}

    def test_links_empty(self):
        hc = HostConfig(links=[])
        assert hc.json() == {'Links': []}

    def test_lxc_conf(self):
        hc = HostConfig(lxc_conf={'lxc.utsname': 'docker'})
        assert hc.json() == {'LxcConf': {'lxc.utsname': 'docker'}}

    def test_memory(self):
        hc = HostConfig(memory=1024)
        assert hc.json(api_version=(1, 18)) == {'Memory': 1024}

    def test_memory_0(self):
        hc = HostConfig(memory=0)
        assert hc.json(api_version=(1, 18)) == {'Memory': 0}

    def test_memory_negative(self):
        with pytest.raises(ValueError):
            HostConfig(memory=-1)

    def test_memory_not_supported(self):
        hc = HostConfig(memory=1024)
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 17))

    def test_swap(self):
        hc = HostConfig(memory=1024, swap=1024)
        assert hc.json(api_version=(1, 18)) == {
            'Memory': 1024, 'MemorySwap': 2048}

    def test_swap_unlimited(self):
        hc = HostConfig(memory=1024, swap=-1)
        assert hc.json(api_version=(1, 18)) == {
            'Memory': 1024, 'MemorySwap': -1}

    def test_swap_without_memory(self):
        with pytest.raises(ValueError):
            HostConfig(swap=1024)

    def test_swap_0(self):
        with pytest.raises(ValueError):
            HostConfig(memory=1024, swap=0)

    def test_swap_not_supported(self):
        hc = HostConfig(memory=1024, swap=1024)
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 17))

    def test_memory_reservation(self):
        hc = HostConfig(memory_reservation=1024)
        assert hc.json(api_version=(1, 21)) == {'MemoryReservation': 1024}

    def test_memory_reservation_negative(self):
        with pytest.raises(ValueError):
            HostConfig(memory_reservation=-1)

    def test_memory_reservation_not_supported(self):
        hc = HostConfig(memory_reservation=1024)
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 20))

    def test_kernel_memory(self):
        hc = HostConfig(kernel_memory=1024)
        assert hc.json(api_version=(1, 21)) == {'KernelMemory': 1024}

    def test_kernel_memory_negative(self):
        with pytest.raises(ValueError):
            HostConfig(kernel_memory=-1)

    def test_kernel_memory_not_supported(self):
        hc = HostConfig(kernel_memory=1024)
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 20))

    def test_cpu_shares(self):
        hc = HostConfig(cpu_shares=42)
        assert hc.json(api_version=(1, 18)) == {'CpuShares': 42}

    def test_cpu_shares_0(self):
        with pytest.raises(ValueError):
            HostConfig(cpu_shares=0)

    def test_cpu_shares_negative(self):
        with pytest.raises(ValueError):
            HostConfig(cpu_shares=-1)

    def test_cpu_shares_not_supported(self):
        hc = HostConfig(cpu_shares=42)
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 17))

    def test_cpu_period(self):
        hc = HostConfig(cpu_period=42)
        assert hc.json(api_version=(1, 19)) == {'CpuPeriod': 42}

    def test_cpu_period_0(self):
        with pytest.raises(ValueError):
            HostConfig(cpu_period=0)

    def test_cpu_period_negative(self):
        with pytest.raises(ValueError):
            HostConfig(cpu_period=-1)

    def test_cpu_period_not_supported(self):
        hc = HostConfig(cpu_period=42)
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 18))

    def test_cpu_quota(self):
        hc = HostConfig(cpu_quota=42)
        assert hc.json(api_version=(1, 19)) == {'CpuQuota': 42}

    def test_cpu_quota_0(self):
        with pytest.raises(ValueError):
            HostConfig(cpu_quota=0)

    def test_cpu_quota_negative(self):
        with pytest.raises(ValueError):
            HostConfig(cpu_quota=-1)

    def test_cpu_quota_not_supported(self):
        hc = HostConfig(cpu_quota=42)
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 18))

    def test_cpuset_cpus_single_digit_0(self):
        hc = HostConfig(cpuset_cpus='0')
        assert hc.json(api_version=(1, 18)) == {'CpusetCpus': '0'}

    def test_cpuset_cpus_single_digit_1(self):
        hc = HostConfig(cpuset_cpus='1')
        assert hc.json(api_version=(1, 18)) == {'CpusetCpus': '1'}

    def test_cpuset_cpus_single_digit_9(self):
        hc = HostConfig(cpuset_cpus='9')
        assert hc.json(api_version=(1, 18)) == {'CpusetCpus': '9'}

    def test_cpuset_cpus_double_digit_42(self):
        hc = HostConfig(cpuset_cpus='42')
        assert hc.json(api_version=(1, 18)) == {'CpusetCpus': '42'}

    def test_cpuset_cpus_double_digit_09(self):
        with pytest.raises(ValueError):
            HostConfig(cpuset_cpus='09')

    def test_cpuset_cpus_many_digits_1234(self):
        hc = HostConfig(cpuset_cpus='1234')
        assert hc.json(api_version=(1, 18)) == {'CpusetCpus': '1234'}

    def test_cpuset_cpus_two_numbers_42_43(self):
        hc = HostConfig(cpuset_cpus='42,43')
        assert hc.json(api_version=(1, 18)) == {'CpusetCpus': '42,43'}

    def test_cpuset_cpus_two_numbers_42_09(self):
        with pytest.raises(ValueError):
            HostConfig(cpuset_cpus='42,09')

    def test_cpuset_cpus_four_numbers(self):
        hc = HostConfig(cpuset_cpus='42,43,1024,147')
        assert hc.json(api_version=(1, 18)) == {'CpusetCpus': '42,43,1024,147'}

    def test_cpuset_cpus_range(self):
        hc = HostConfig(cpuset_cpus='0-4')
        assert hc.json(api_version=(1, 18)) == {'CpusetCpus': '0-4'}

    def test_cpuset_cpus_range_and_numbers_1(self):
        hc = HostConfig(cpuset_cpus='0-4,7')
        assert hc.json(api_version=(1, 18)) == {'CpusetCpus': '0-4,7'}

    def test_cpuset_cpus_range_and_numbers_2(self):
        hc = HostConfig(cpuset_cpus='0,4-7')
        assert hc.json(api_version=(1, 18)) == {'CpusetCpus': '0,4-7'}

    def test_cpuset_cpus_starting_with_comma(self):
        with pytest.raises(ValueError):
            HostConfig(cpuset_cpus=',42')

    def test_cpuset_cpus_ending_with_comma(self):
        with pytest.raises(ValueError):
            HostConfig(cpuset_cpus='42,')

    def test_cpuset_cpus_word(self):
        with pytest.raises(ValueError):
            HostConfig(cpuset_cpus='bar')

    def test_cpuset_cpus_name_with_caps(self):
        with pytest.raises(ValueError):
            HostConfig(cpuset_cpus='BAR')

    def test_cpuset_cpus_name_with_number(self):
        with pytest.raises(ValueError):
            HostConfig(cpuset_cpus='foo2bar')

    def test_cpuset_cpus_name_starting_with_number(self):
        with pytest.raises(ValueError):
            HostConfig(cpuset_cpus='2bar')

    def test_cpuset_cpus_number_and_semicolon(self):
        with pytest.raises(ValueError):
            HostConfig(cpuset_cpus='42;43')

    def test_cpuset_cpus_number_and_hash(self):
        with pytest.raises(ValueError):
            HostConfig(cpuset_cpus='42#43')

    def test_cpuset_cpus_number_and_dollar(self):
        with pytest.raises(ValueError):
            HostConfig(cpuset_cpus='42$43')

    def test_cpuset_cpus_not_not_str(self):
        hc = HostConfig(cpuset_cpus=Cpuset("42"))
        assert hc.json(api_version=(1, 18)) == {'CpusetCpus': '42'}

    def test_cpuset_cpus_not_supported(self):
        hc = HostConfig(cpuset_cpus='42')
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 17))

    def test_cpuset_mems(self):
        hc = HostConfig(cpuset_mems=Cpuset('42'))
        assert hc.json(api_version=(1, 19)) == {'CpusetMems': '42'}

    def test_cpuset_mems_two_numbers(self):
        hc = HostConfig(cpuset_mems='42,43')
        assert hc.json(api_version=(1, 19)) == {'CpusetMems': '42,43'}

    def test_cpuset_mems_range(self):
        hc = HostConfig(cpuset_mems='0-4')
        assert hc.json(api_version=(1, 19)) == {'CpusetMems': '0-4'}

    def test_cpuset_mems_not_str(self):
        hc = HostConfig(cpuset_mems='42')
        assert hc.json(api_version=(1, 19)) == {'CpusetMems': '42'}

    def test_cpuset_mems_not_supported(self):
        hc = HostConfig(cpuset_mems='42')
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 18))

    def test_blkio_weight_10_to_1000(self):
        for i in range(10, 1000+1):
            hc = HostConfig(blkio_weight=i)
            assert hc.json(api_version=(1, 19)) == {'BlkioWeight': i}

    def test_blkio_weight_9(self):
        with pytest.raises(ValueError):
            HostConfig(blkio_weight=9)

    def test_blkio_weight_0(self):
        with pytest.raises(ValueError):
            HostConfig(blkio_weight=0)

    def test_blkio_weight_negative(self):
        with pytest.raises(ValueError):
            HostConfig(blkio_weight=-1)

    def test_blkio_weight_1001(self):
        with pytest.raises(ValueError):
            HostConfig(blkio_weight=1001)

    def test_blkio_weight_not_supported(self):
        hc = HostConfig(blkio_weight=10)
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 18))

    def test_memory_swappiness_valid(self):
        for i in range(0, 100+1):
            hc = HostConfig(memory_swappiness=i)
            assert hc.json(api_version=(1, 20)) == {'MemorySwappiness': i}

    def test_memory_swappiness_negative(self):
        with pytest.raises(ValueError):
            HostConfig(memory_swappiness=-1)

    def test_memory_swappiness_101(self):
        with pytest.raises(ValueError):
            HostConfig(memory_swappiness=1001)

    def test_memory_swappiness_not_supported(self):
        hc = HostConfig(memory_swappiness=10)
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 19))

    def test_oom_kill_true(self):
        hc = HostConfig(oom_kill=True)
        assert hc.json(api_version=(1, 19)) == {'OomKillDisable': False}

    def test_oom_kill_false(self):
        hc = HostConfig(oom_kill=False)
        assert hc.json(api_version=(1, 19)) == {'OomKillDisable': True}

    def test_oom_kill_not_supported(self):
        hc = HostConfig(oom_kill=False)
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 18))

    def test_port_bindings_empty(self):
        hc = HostConfig(port_bindings=[])
        assert hc.json() == {'PortBindings': {}}

    def test_port_bindings(self):
        hc = HostConfig(port_bindings=[PortBinding(22)])
        assert hc.json() == {'PortBindings': {'22/tcp': [{'HostPort': '22'}]}}

    def test_port_bindings_tcp(self):
        hc = HostConfig(port_bindings=[PortBinding(22, 'tcp')])
        assert hc.json() == {'PortBindings': {'22/tcp': [{'HostPort': '22'}]}}

    def test_port_bindings_udp(self):
        hc = HostConfig(port_bindings=[PortBinding(22, 'udp')])
        assert hc.json() == {'PortBindings': {'22/udp': [{'HostPort': '22'}]}}

    def test_port_bindings_invalid_protocol(self):
        with pytest.raises(ValueError):
            HostConfig(port_bindings=[PortBinding(22, 'foobar')])

    def test_port_bindings_port_0(self):
        with pytest.raises(ValueError):
            HostConfig(port_bindings=[PortBinding(0)])

    def test_port_bindings_port_negative(self):
        with pytest.raises(ValueError):
            HostConfig(port_bindings=[PortBinding(-1)])

    def test_port_bindings_large(self):
        hc = HostConfig(port_bindings=[PortBinding(65535)])
        assert hc.json() == {'PortBindings': {
            '65535/tcp': [{'HostPort': '65535'}]}}

    def test_port_bindings_port_large_invalid(self):
        with pytest.raises(ValueError):
            HostConfig(port_bindings=[PortBinding(65536)])

    def test_port_bindings_host_port(self):
        hc = HostConfig(port_bindings=[
            PortBinding(22, 'tcp', host_port=10022)])
        assert hc.json() == {'PortBindings': {
            '22/tcp': [{'HostPort': '10022'}]}}

    def test_port_bindings_host_ip(self):
        hc = HostConfig(port_bindings=[
            PortBinding(22, 'tcp', host_ip='192.168.1.2')])
        assert hc.json() == {'PortBindings': {
            '22/tcp': [{'HostIp': '192.168.1.2', 'HostPort': '22'}]}}

    def test_port_bindings_2(self):
        hc = HostConfig(port_bindings=[
            PortBinding(22, 'tcp', host_ip='192.168.1.2'),
            PortBinding(23, 'udp', host_ip='192.168.1.3')])
        assert hc.json() == {'PortBindings': {
            '22/tcp': [{'HostIp': '192.168.1.2', 'HostPort': '22'}],
            '23/udp': [{'HostIp': '192.168.1.3', 'HostPort': '23'}]}}

    def test_publish_all_ports_true(self):
        hc = HostConfig(publish_all_ports=True)
        assert hc.json() == {'PublishAllPorts': True}

    def test_publish_all_ports_false(self):
        hc = HostConfig(publish_all_ports=False)
        assert hc.json() == {'PublishAllPorts': False}

    def test_privileged_true(self):
        hc = HostConfig(privileged=True)
        assert hc.json() == {'Privileged': True}

    def test_privileged_false(self):
        hc = HostConfig(privileged=False)
        assert hc.json() == {'Privileged': False}

    def test_read_only_rootfs_true(self):
        hc = HostConfig(read_only_rootfs=True)
        assert hc.json(api_version=(1, 17)) == {'ReadonlyRootfs': True}

    def test_read_only_rootfs_false(self):
        hc = HostConfig(read_only_rootfs=False)
        assert hc.json(api_version=(1, 17)) == {'ReadonlyRootfs': False}

    def test_read_only_rootfs_not_supported(self):
        hc = HostConfig(read_only_rootfs=True)
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 16))

    def test_dns_empty(self):
        hc = HostConfig(dns=[])
        assert hc.json() == {'Dns': []}

    def test_dns_1(self):
        hc = HostConfig(dns=['192.168.1.2'])
        assert hc.json() == {'Dns': ['192.168.1.2']}

    def test_dns_2(self):
        hc = HostConfig(dns=['192.168.1.2', '192.168.1.3'])
        assert hc.json() == {'Dns': ['192.168.1.2', '192.168.1.3']}

    def test_dns_invalid(self):
        with pytest.raises(ValueError):
            HostConfig(dns=['192.168.1.2x'])

    def test_dns_options_0(self):
        hc = HostConfig(dns_options=[])
        assert hc.json(api_version=(1, 21)) == {'DnsOptions': []}

    def test_dns_options_1_empty(self):
        hc = HostConfig(dns_options=[''])
        assert hc.json(api_version=(1, 21)) == {'DnsOptions': ['']}

    def test_dns_options_1(self):
        hc = HostConfig(dns_options=['foo'])
        assert hc.json(api_version=(1, 21)) == {'DnsOptions': ['foo']}

    def test_dns_options_2(self):
        hc = HostConfig(dns_options=['foo', 'bar'])
        assert hc.json(api_version=(1, 21)) == {'DnsOptions': ['foo', 'bar']}

    def test_dns_options_not_supported(self):
        hc = HostConfig(dns_options=['foo'])
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 20))

    def test_dns_search_0(self):
        hc = HostConfig(dns_search=[])
        assert hc.json(api_version=(1, 15)) == {'DnsSearch': []}

    def test_dns_search_1_empty(self):
        hc = HostConfig(dns_search=[''])
        assert hc.json(api_version=(1, 15)) == {'DnsSearch': ['']}

    def test_dns_search_1(self):
        hc = HostConfig(dns_search=['foo.com'])
        assert hc.json(api_version=(1, 15)) == {'DnsSearch': ['foo.com']}

    def test_dns_search_2(self):
        hc = HostConfig(dns_search=['foo.com', 'bar.org'])
        assert hc.json(api_version=(1, 15)) == {
            'DnsSearch': ['foo.com', 'bar.org']}

    def test_dns_search_not_supported(self):
        hc = HostConfig(dns_search=['foo.com'])
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 14))

    def test_extra_hosts_0(self):
        hc = HostConfig(extra_hosts=[])
        assert hc.json(api_version=(1, 15)) == {'ExtraHosts': []}

    def test_extra_hosts_1(self):
        hc = HostConfig(extra_hosts=[
            HostnameIPMapping('foo.com', '192.168.1.2')])
        assert hc.json(api_version=(1, 15)) == {
            'ExtraHosts': ['foo.com:192.168.1.2']}

    def test_extra_hosts_2(self):
        hc = HostConfig(extra_hosts=[
            HostnameIPMapping('foo.com', '192.168.1.2'),
            HostnameIPMapping('bar.org', '10.0.0.1')])
        assert hc.json(api_version=(1, 15)) == {
            'ExtraHosts': ['foo.com:192.168.1.2', 'bar.org:10.0.0.1']}

    def test_extra_hosts_str(self):
        hc = HostConfig(extra_hosts=['foo.com:192.168.1.2'])
        assert hc.json(api_version=(1, 15)) == {
            'ExtraHosts': ['foo.com:192.168.1.2']}

    def test_extra_hosts_str_invalid_1(self):
        with pytest.raises(ValueError):
            HostConfig(extra_hosts=['foo.com'])

    def test_extra_hosts_str_invalid_2(self):
        with pytest.raises(ValueError):
            HostConfig(extra_hosts=['foo.com:bar:x'])

    def test_extra_hosts_not_supported(self):
        hc = HostConfig(extra_hosts=[
            HostnameIPMapping('foo.com', '192.168.1.2')])
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 14))

    def test_group_add_0(self):
        hc = HostConfig(group_add=[])
        assert hc.json(api_version=(1, 20)) == {'GroupAdd': []}

    def test_group_add_1(self):
        hc = HostConfig(group_add=['foo'])
        assert hc.json(api_version=(1, 20)) == {'GroupAdd': ['foo']}

    def test_group_add_2(self):
        hc = HostConfig(group_add=['foo', 'bar'])
        assert hc.json(api_version=(1, 20)) == {'GroupAdd': ['foo', 'bar']}

    def test_group_add_not_supported(self):
        hc = HostConfig(group_add=['foo'])
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 19))

    def test_volumes_from_empty(self):
        hc = HostConfig(volumes_from=[])
        assert hc.json() == {'VolumesFrom': []}

    def test_volumes_from_str(self):
        hc = HostConfig(volumes_from=['foo'])
        assert hc.json() == {'VolumesFrom': ['foo']}

    def test_volumes_from_instance_1(self):
        hc = HostConfig(volumes_from=[VolumesFrom('foo')])
        assert hc.json() == {'VolumesFrom': ['foo']}

    def test_volumes_from_instance_ro(self):
        hc = HostConfig(volumes_from=[VolumesFrom('foo', ro=True)])
        assert hc.json() == {'VolumesFrom': ['foo:ro']}

    def test_volumes_from_instance_rw(self):
        hc = HostConfig(volumes_from=[VolumesFrom('foo', ro=False)])
        assert hc.json() == {'VolumesFrom': ['foo:rw']}

    def test_cap_add_0(self):
        hc = HostConfig(cap_add=[])
        assert hc.json() == {'CapAdd': []}

    def test_cap_add_1(self):
        hc = HostConfig(cap_add=['foo'])
        assert hc.json() == {'CapAdd': ['foo']}

    def test_cap_add_2(self):
        hc = HostConfig(cap_add=['foo', 'bar'])
        assert hc.json() == {'CapAdd': ['foo', 'bar']}

    def test_cap_drop_0(self):
        hc = HostConfig(cap_drop=[])
        assert hc.json() == {'CapDrop': []}

    def test_cap_drop_1(self):
        hc = HostConfig(cap_drop=['foo'])
        assert hc.json() == {'CapDrop': ['foo']}

    def test_cap_drop_2(self):
        hc = HostConfig(cap_drop=['foo', 'bar'])
        assert hc.json() == {'CapDrop': ['foo', 'bar']}

    def test_restart_policy_always(self):
        hc = HostConfig(restart_policy='always')
        assert hc.json(api_version=(1, 15)) == {
            'RestartPolicy': {'Name': 'always'}}

    def test_restart_policy_unless_stopped(self):
        hc = HostConfig(restart_policy='unless-stopped')
        assert hc.json(api_version=(1, 15)) == {
            'RestartPolicy': {'Name': 'unless-stopped'}}

    def test_restart_policy_on_failure_42(self):
        hc = HostConfig(restart_policy=RestartPolicy('on-failure', 42))
        assert hc.json(api_version=(1, 15)) == {
            'RestartPolicy': {'Name': 'on-failure',
                              'MaximumRetryCount': 42}}

    def test_restart_policy_invalid(self):
        with pytest.raises(ValueError):
            HostConfig(restart_policy='foo')

    def test_restart_policy_not_supported(self):
        hc = HostConfig(restart_policy='always')
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 14))

    def test_network_mode(self):
        hc = HostConfig(network_mode='foo')
        assert hc.json(api_version=(1, 15)) == {'NetworkMode': 'foo'}

    def test_network_mode_not_supported(self):
        hc = HostConfig(network_mode=['foo'])
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 14))

    def test_devices_empty(self):
        hc = HostConfig(devices=[])
        assert hc.json(api_version=(1, 15)) == {'Devices': []}

    def test_devices_str(self):
        hc = HostConfig(devices=['/dev/foo'])
        assert hc.json(api_version=(1, 15)) == {'Devices': [
            {'PathOnHost': '/dev/foo',
             'PathInContainer': '/dev/foo',
             'CgroupPermissions': 'rwm'}]}

    def test_devices_instance(self):
        hc = HostConfig(devices=[DeviceToAdd('/dev/foo', '/dev/bar')])
        assert hc.json(api_version=(1, 15)) == {'Devices': [
            {'PathOnHost': '/dev/foo',
             'PathInContainer': '/dev/bar',
             'CgroupPermissions': 'rwm'}]}

    def test_devices_not_supported(self):
        hc = HostConfig(devices=['/dev/foo'])
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 14))

    def test_ulimits_empty(self):
        hc = HostConfig(ulimits=[])
        assert hc.json(api_version=(1, 18)) == {'Ulimits': []}

    def test_ulimits_instance(self):
        hc = HostConfig(ulimits=[Ulimit('nofile', 1024, 2048)])
        assert hc.json(api_version=(1, 18)) == {'Ulimits': [
            {'Name': 'nofile',
             'Soft': 1024,
             'Hard': 2048}]}

    def test_ulimits_not_supported(self):
        hc = HostConfig(ulimits=[Ulimit('nofile', 1024, 2048)])
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 17))

    def test_log_config(self):
        hc = HostConfig(log_config=LogConfiguration('json-file'))
        assert hc.json(api_version=(1, 18)) == {'LogConfig': {
            'Type': 'json-file',
            'Config': None}}

    def test_log_config_not_supported(self):
        hc = HostConfig(log_config=LogConfiguration('json-file'))
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 17))

    def test_security_opt_empty(self):
        hc = HostConfig(security_opt=[])
        assert hc.json(api_version=(1, 17)) == {'SecurityOpt': []}

    def test_security_opt_foo(self):
        hc = HostConfig(security_opt=['foo'])
        assert hc.json(api_version=(1, 17)) == {'SecurityOpt': ['foo']}

    def test_security_opt_foobar(self):
        hc = HostConfig(security_opt=['foo', 'bar'])
        assert hc.json(api_version=(1, 17)) == {'SecurityOpt': ['foo', 'bar']}

    def test_security_opt_not_supported(self):
        hc = HostConfig(security_opt=[])
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 16))

    def test_cgroup_parent_absolute(self):
        hc = HostConfig(cgroup_parent='/foo')
        assert hc.json(api_version=(1, 18)) == {'CgroupParent': '/foo'}

    def test_cgroup_parent_relative(self):
        hc = HostConfig(cgroup_parent='foo')
        assert hc.json(api_version=(1, 18)) == {'CgroupParent': 'foo'}

    def test_cgroup_parent_not_supported(self):
        hc = HostConfig(cgroup_parent='/foo')
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 17))

    def test_volume_driver_foo(self):
        hc = HostConfig(volume_driver='foo')
        assert hc.json(api_version=(1, 21)) == {'VolumeDriver': 'foo'}

    def test_volume_driver_not_supported(self):
        hc = HostConfig(volume_driver='foo')
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 20))

    def test_shm_size_42(self):
        hc = HostConfig(shm_size=42)
        assert hc.json(api_version=(1, 22)) == {'ShmSize': 42}

    def test_shm_size_not_supported(self):
        hc = HostConfig(shm_size=42)
        with pytest.raises(ValueError):
            hc.json(api_version=(1, 21))
