import unittest
import mock

from xd.docker.parameters import *


class ParametersTestCase(unittest.case.TestCase):

    def setUp(self):
        self.d = {}


class set_integer_tests(ParametersTestCase):

    def test_0(self):
        set_integer(self.d, 'foo', 0)
        self.assertEqual(self.d, {'foo': 0})

    def test_42(self):
        set_integer(self.d, 'foo', 42)
        self.assertEqual(self.d, {'foo': 42})

    def test_minus_42(self):
        set_integer(self.d, 'foo', -42)
        self.assertEqual(self.d, {'foo': -42})

    def test_none(self):
        set_integer(self.d, 'foo', None)
        self.assertEqual(self.d, {})

    def test_string(self):
        with self.assertRaises(TypeError):
            set_integer(self.d, 'foo', '42')

    def test_boolean(self):
        with self.assertRaises(TypeError):
            set_integer(self.d, 'foo', True)

    def test_list(self):
        with self.assertRaises(TypeError):
            set_integer(self.d, 'foo', [42])

    def test_dict(self):
        with self.assertRaises(TypeError):
            set_integer(self.d, 'foo', {'foo': 42})

    def test_min_ok(self):
        set_integer(self.d, 'foo', 42, min=0)

    def test_min_error(self):
        with self.assertRaises(ValueError):
            set_integer(self.d, 'foo', 42, min=100)

    def test_max_ok(self):
        set_integer(self.d, 'foo', 42, max=100)

    def test_max_error(self):
        with self.assertRaises(ValueError):
            set_integer(self.d, 'foo', 42, max=10)


class set_boolean_tests(ParametersTestCase):

    def test_true(self):
        set_boolean(self.d, 'foo', True)
        self.assertEqual(self.d, {'foo': True})

    def test_false(self):
        set_boolean(self.d, 'foo', False)
        self.assertEqual(self.d, {'foo': False})

    def test_none(self):
        set_boolean(self.d, 'foo', None)
        self.assertEqual(self.d, {})

    def test_int(self):
        with self.assertRaises(TypeError):
            set_boolean(self.d, 'foo', 42)

    def test_string(self):
        with self.assertRaises(TypeError):
            set_boolean(self.d, 'foo', 'True')

    def test_list(self):
        with self.assertRaises(TypeError):
            set_boolean(self.d, 'foo', [True])

    def test_dict(self):
        with self.assertRaises(TypeError):
            set_boolean(self.d, 'foo', {'foo': True})


class set_string_tests(ParametersTestCase):

    def test_bar(self):
        set_string(self.d, 'foo', 'bar')
        self.assertEqual(self.d, {'foo': 'bar'})

    def test_empty(self):
        set_string(self.d, 'foo', '')
        self.assertEqual(self.d, {'foo': ''})

    def test_none(self):
        set_string(self.d, 'foo', None)
        self.assertEqual(self.d, {})

    def test_int(self):
        with self.assertRaises(TypeError):
            set_string(self.d, 'foo', 42)

    def test_boolean(self):
        with self.assertRaises(TypeError):
            set_string(self.d, 'foo', True)

    def test_list(self):
        with self.assertRaises(TypeError):
            set_string(self.d, 'foo', ['bar'])

    def test_dict(self):
        with self.assertRaises(TypeError):
            set_string(self.d, 'foo', {'foo': 'bar'})


class set_list_of_strings_tests(ParametersTestCase):

    def test_bar(self):
        set_list_of_strings(self.d, 'foo', ['bar'])
        self.assertEqual(self.d, {'foo': ['bar']})

    def test_empty_string(self):
        set_list_of_strings(self.d, 'foo', [''])
        self.assertEqual(self.d, {'foo': ['']})

    def test_empty(self):
        set_list_of_strings(self.d, 'foo', [])
        self.assertEqual(self.d, {'foo': []})

    def test_none(self):
        set_list_of_strings(self.d, 'foo', None)
        self.assertEqual(self.d, {})

    def test_int(self):
        with self.assertRaises(TypeError):
            set_list_of_strings(self.d, 'foo', 42)

    def test_boolean(self):
        with self.assertRaises(TypeError):
            set_list_of_strings(self.d, 'foo', True)

    def test_string(self):
        with self.assertRaises(TypeError):
            set_list_of_strings(self.d, 'foo', 'bar')

    def test_dict(self):
        with self.assertRaises(TypeError):
            set_list_of_strings(self.d, 'foo', {'foo': 'bar'})

    def test_list_with_int(self):
        with self.assertRaises(ValueError):
            set_list_of_strings(self.d, 'foo', [42])

    def test_list_with_int_mixed(self):
        with self.assertRaises(ValueError):
            set_list_of_strings(self.d, 'foo', ['bar', 42])

    def test_list_with_boolean(self):
        with self.assertRaises(ValueError):
            set_list_of_strings(self.d, 'foo', [True])

    def test_list_with_boolean_mixed(self):
        with self.assertRaises(ValueError):
            set_list_of_strings(self.d, 'foo', ['bar', True])


class set_string_or_list_of_strings_tests(ParametersTestCase):

    def test_bar(self):
        set_string_or_list_of_strings(self.d, 'foo', 'bar')
        self.assertEqual(self.d, {'foo': 'bar'})

    def test_empty_string(self):
        set_string_or_list_of_strings(self.d, 'foo', '')
        self.assertEqual(self.d, {'foo': ''})

    def test_empty_list(self):
        set_string_or_list_of_strings(self.d, 'foo', [])
        self.assertEqual(self.d, {'foo': []})

    def test_list_of_string(self):
        set_string_or_list_of_strings(self.d, 'foo', ['bar'])
        self.assertEqual(self.d, {'foo': ['bar']})

    def test_list_of_empty_string(self):
        set_string_or_list_of_strings(self.d, 'foo', [''])
        self.assertEqual(self.d, {'foo': ['']})

    def test_none(self):
        set_string_or_list_of_strings(self.d, 'foo', None)
        self.assertEqual(self.d, {})

    def test_int(self):
        with self.assertRaises(TypeError):
            set_string_or_list_of_strings(self.d, 'foo', 42)

    def test_boolean(self):
        with self.assertRaises(TypeError):
            set_string_or_list_of_strings(self.d, 'foo', True)

    def test_dict(self):
        with self.assertRaises(TypeError):
            set_string_or_list_of_strings(self.d, 'foo', {'foo': 'bar'})

    def test_list_with_int(self):
        with self.assertRaises(ValueError):
            set_string_or_list_of_strings(self.d, 'foo', [42])

    def test_list_with_int_mixed(self):
        with self.assertRaises(ValueError):
            set_string_or_list_of_strings(self.d, 'foo', ['bar', 42])

    def test_list_with_boolean(self):
        with self.assertRaises(ValueError):
            set_string_or_list_of_strings(self.d, 'foo', [True])

    def test_list_with_boolean_mixed(self):
        with self.assertRaises(ValueError):
            set_string_or_list_of_strings(self.d, 'foo', ['bar', True])


class set_dict_of_strings_tests(ParametersTestCase):

    def test_foobar(self):
        set_dict_of_strings(self.d, 'foo', {'bar': 'foobar'})
        self.assertEqual(self.d, {'foo': {'bar': 'foobar'}})

    def test_empty_string(self):
        set_dict_of_strings(self.d, 'foo', {'bar': ''})
        self.assertEqual(self.d, {'foo': {'bar': ''}})

    def test_empty(self):
        set_dict_of_strings(self.d, 'foo', {})
        self.assertEqual(self.d, {'foo': {}})

    def test_none(self):
        set_dict_of_strings(self.d, 'foo', None)
        self.assertEqual(self.d, {})

    def test_int(self):
        with self.assertRaises(TypeError):
            set_dict_of_strings(self.d, 'foo', 42)

    def test_boolean(self):
        with self.assertRaises(TypeError):
            set_dict_of_strings(self.d, 'foo', True)

    def test_string(self):
        with self.assertRaises(TypeError):
            set_dict_of_strings(self.d, 'foo', 'bar')

    def test_dict_with_int(self):
        with self.assertRaises(ValueError):
            set_dict_of_strings(self.d, 'foo', {'bar': 42})

    def test_list_with_int_mixed(self):
        with self.assertRaises(ValueError):
            set_dict_of_strings(self.d, 'foo', {'bar': 'foobar', 'i': 42})

    def test_list_with_boolean(self):
        with self.assertRaises(ValueError):
            set_dict_of_strings(self.d, 'foo', {'bar': True})

    def test_list_with_boolean_mixed(self):
        with self.assertRaises(ValueError):
            set_dict_of_strings(self.d, 'foo', {'bar': 'foobar', 'b': True})


class set_container_name_tests(ParametersTestCase):

    def test_name(self):
        set_container_name(self.d, 'foo', 'bar')
        self.assertEqual(self.d, {'foo': 'bar'})

    def test_name_with_caps(self):
        set_container_name(self.d, 'foo', 'BAR')
        self.assertEqual(self.d, {'foo': 'BAR'})

    def test_name_with_number(self):
        set_container_name(self.d, 'foo', 'bar2')
        self.assertEqual(self.d, {'foo': 'bar2'})

    def test_name_with_underscore(self):
        set_container_name(self.d, 'foo', 'foo_bar')
        self.assertEqual(self.d, {'foo': 'foo_bar'})

    def test_name_with_dash(self):
        set_container_name(self.d, 'foo', 'foo-bar')
        self.assertEqual(self.d, {'foo': 'foo-bar'})

    def test_none(self):
        set_container_name(self.d, 'foo', None)
        self.assertEqual(self.d, {})

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            set_container_name(self.d, 'foo', '')

    def test_int(self):
        with self.assertRaises(TypeError):
            set_container_name(self.d, 'foo', 42)

    def test_list(self):
        with self.assertRaises(TypeError):
            set_container_name(self.d, 'foo', ['bar'])

    def test_dict(self):
        with self.assertRaises(TypeError):
            set_container_name(self.d, 'foo', {'bar': 'foobar'})

    def test_boolean(self):
        with self.assertRaises(TypeError):
            set_container_name(self.d, 'foo', True)


class set_image_name_tests(ParametersTestCase):

    def test_bar(self):
        set_image_name(self.d, 'foo', 'bar')
        self.assertEqual(self.d, {'foo': 'bar'})

    def test_empty(self):
        with self.assertRaises(ValueError):
            set_image_name(self.d, 'foo', '')

    def test_none(self):
        set_image_name(self.d, 'foo', None)
        self.assertEqual(self.d, {})

    def test_int(self):
        with self.assertRaises(TypeError):
            set_image_name(self.d, 'foo', 42)

    def test_boolean(self):
        with self.assertRaises(TypeError):
            set_image_name(self.d, 'foo', True)

    def test_list(self):
        with self.assertRaises(TypeError):
            set_image_name(self.d, 'foo', ['bar'])

    def test_dict(self):
        with self.assertRaises(TypeError):
            set_image_name(self.d, 'foo', {'foo': 'bar'})


class set_hostname_tests(ParametersTestCase):

    def test_name(self):
        set_hostname(self.d, 'foo', 'bar')
        self.assertEqual(self.d, {'foo': 'bar'})

    def test_name_with_caps(self):
        with self.assertRaises(ValueError):
            set_hostname(self.d, 'foo', 'BAR')

    def test_name_with_number(self):
        set_hostname(self.d, 'foo', 'foo2bar')
        self.assertEqual(self.d, {'foo': 'foo2bar'})

    def test_name_starting_with_number(self):
        set_hostname(self.d, 'foo', '2bar')
        self.assertEqual(self.d, {'foo': '2bar'})

    def test_name_with_underscore(self):
        with self.assertRaises(ValueError):
            set_hostname(self.d, 'foo', 'foo_bar')

    def test_name_with_dash(self):
        set_hostname(self.d, 'foo', 'foo-bar')
        self.assertEqual(self.d, {'foo': 'foo-bar'})

    def test_name_starting_with_dash(self):
        with self.assertRaises(ValueError):
            set_hostname(self.d, 'foo', '-bar')

    def test_name_with_dot(self):
        with self.assertRaises(ValueError):
            set_hostname(self.d, 'foo', 'foo.bar')

    def test_none(self):
        set_hostname(self.d, 'foo', None)
        self.assertEqual(self.d, {})

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            set_hostname(self.d, 'foo', '')

    def test_int(self):
        with self.assertRaises(TypeError):
            set_hostname(self.d, 'foo', 42)

    def test_list(self):
        with self.assertRaises(TypeError):
            set_hostname(self.d, 'foo', ['bar'])

    def test_dict(self):
        with self.assertRaises(TypeError):
            set_hostname(self.d, 'foo', {'bar': 'foobar'})

    def test_boolean(self):
        with self.assertRaises(TypeError):
            set_hostname(self.d, 'foo', True)


class set_domainname_tests(ParametersTestCase):

    def test_name(self):
        set_domainname(self.d, 'foo', 'bar')
        self.assertEqual(self.d, {'foo': 'bar'})

    def test_name_with_caps(self):
        with self.assertRaises(ValueError):
            set_domainname(self.d, 'foo', 'BAR')

    def test_name_with_number(self):
        set_domainname(self.d, 'foo', 'foo2bar')
        self.assertEqual(self.d, {'foo': 'foo2bar'})

    def test_name_starting_with_number(self):
        set_domainname(self.d, 'foo', '2bar')
        self.assertEqual(self.d, {'foo': '2bar'})

    def test_name_with_underscore(self):
        with self.assertRaises(ValueError):
            set_domainname(self.d, 'foo', 'foo_bar')

    def test_name_with_dash(self):
        set_domainname(self.d, 'foo', 'foo-bar')
        self.assertEqual(self.d, {'foo': 'foo-bar'})

    def test_name_starting_with_dash(self):
        with self.assertRaises(ValueError):
            set_domainname(self.d, 'foo', '-bar')

    def test_name_with_dot(self):
        set_domainname(self.d, 'foo', 'foo.bar')
        self.assertEqual(self.d, {'foo': 'foo.bar'})

    def test_none(self):
        set_domainname(self.d, 'foo', None)
        self.assertEqual(self.d, {})

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            set_domainname(self.d, 'foo', '')

    def test_int(self):
        with self.assertRaises(TypeError):
            set_domainname(self.d, 'foo', 42)

    def test_list(self):
        with self.assertRaises(TypeError):
            set_domainname(self.d, 'foo', ['bar'])

    def test_dict(self):
        with self.assertRaises(TypeError):
            set_domainname(self.d, 'foo', {'bar': 'foobar'})

    def test_boolean(self):
        with self.assertRaises(TypeError):
            set_domainname(self.d, 'foo', True)


class set_user_name_tests(ParametersTestCase):

    def test_name(self):
        set_user_name(self.d, 'foo', 'bar')
        self.assertEqual(self.d, {'foo': 'bar'})

    def test_name_with_caps(self):
        with self.assertRaises(ValueError):
            set_user_name(self.d, 'foo', 'BAR')

    def test_name_with_number(self):
        set_user_name(self.d, 'foo', 'foo2bar')
        self.assertEqual(self.d, {'foo': 'foo2bar'})

    def test_name_starting_with_number(self):
        set_user_name(self.d, 'foo', '2bar')

    def test_name_with_underscore(self):
        set_user_name(self.d, 'foo', 'foo_bar')
        self.assertEqual(self.d, {'foo': 'foo_bar'})

    def test_name_starting_with_underscore(self):
        with self.assertRaises(ValueError):
            set_user_name(self.d, 'foo', '_bar')

    def test_name_with_dash(self):
        set_user_name(self.d, 'foo', 'foo-bar')
        self.assertEqual(self.d, {'foo': 'foo-bar'})

    def test_name_starting_with_dash(self):
        with self.assertRaises(ValueError):
            set_user_name(self.d, 'foo', '-bar')

    def test_name_with_dot(self):
        with self.assertRaises(ValueError):
            set_user_name(self.d, 'foo', 'foo.bar')

    def test_name_with_semicolon(self):
        with self.assertRaises(ValueError):
            set_user_name(self.d, 'foo', 'foo;bar')

    def test_name_with_hash(self):
        with self.assertRaises(ValueError):
            set_user_name(self.d, 'foo', 'foo#bar')

    def test_name_with_dollar(self):
        with self.assertRaises(ValueError):
            set_user_name(self.d, 'foo', 'foo$bar')

    def test_none(self):
        set_user_name(self.d, 'foo', None)
        self.assertEqual(self.d, {})

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            set_user_name(self.d, 'foo', '')

    def test_int(self):
        with self.assertRaises(TypeError):
            set_user_name(self.d, 'foo', 42)

    def test_list(self):
        with self.assertRaises(TypeError):
            set_user_name(self.d, 'foo', ['bar'])

    def test_dict(self):
        with self.assertRaises(TypeError):
            set_user_name(self.d, 'foo', {'bar': 'foobar'})

    def test_boolean(self):
        with self.assertRaises(TypeError):
            set_user_name(self.d, 'foo', True)


class set_cpuset_list_tests(ParametersTestCase):

    def test_single_digit_0(self):
        set_cpuset_list(self.d, 'foo', '0')
        self.assertEqual(self.d, {'foo': '0'})

    def test_single_digit_1(self):
        set_cpuset_list(self.d, 'foo', '1')
        self.assertEqual(self.d, {'foo': '1'})

    def test_single_digit_9(self):
        set_cpuset_list(self.d, 'foo', '9')
        self.assertEqual(self.d, {'foo': '9'})

    def test_double_digit_42(self):
        set_cpuset_list(self.d, 'foo', '42')
        self.assertEqual(self.d, {'foo': '42'})

    def test_double_digit_09(self):
        with self.assertRaises(ValueError):
            set_cpuset_list(self.d, 'foo', '09')

    def test_many_digits_1234(self):
        set_cpuset_list(self.d, 'foo', '1234')
        self.assertEqual(self.d, {'foo': '1234'})

    def test_two_numbers_42_43(self):
        set_cpuset_list(self.d, 'foo', '42,43')
        self.assertEqual(self.d, {'foo': '42,43'})

    def test_two_numbers_42_09(self):
        with self.assertRaises(ValueError):
            set_cpuset_list(self.d, 'foo', '42,09')

    def test_four_numbers(self):
        set_cpuset_list(self.d, 'foo', '42,43,1024,147')
        self.assertEqual(self.d, {'foo': '42,43,1024,147'})

    def test_range(self):
        set_cpuset_list(self.d, 'foo', '0-4')
        self.assertEqual(self.d, {'foo': '0-4'})

    def test_range_and_numbers_1(self):
        set_cpuset_list(self.d, 'foo', '0-4,7')
        self.assertEqual(self.d, {'foo': '0-4,7'})

    def test_range_and_numbers_2(self):
        set_cpuset_list(self.d, 'foo', '0,4-7')
        self.assertEqual(self.d, {'foo': '0,4-7'})

    def test_starting_with_comma(self):
        with self.assertRaises(ValueError):
            set_cpuset_list(self.d, 'foo', ',42')

    def test_ending_with_comma(self):
        with self.assertRaises(ValueError):
            set_cpuset_list(self.d, 'foo', '42,')

    def test_word(self):
        with self.assertRaises(ValueError):
            set_cpuset_list(self.d, 'foo', 'bar')

    def test_name_with_caps(self):
        with self.assertRaises(ValueError):
            set_cpuset_list(self.d, 'foo', 'BAR')

    def test_name_with_number(self):
        with self.assertRaises(ValueError):
            set_cpuset_list(self.d, 'foo', 'foo2bar')

    def test_name_starting_with_number(self):
        with self.assertRaises(ValueError):
            set_cpuset_list(self.d, 'foo', '2bar')

    def test_number_and_semicolon(self):
        with self.assertRaises(ValueError):
            set_cpuset_list(self.d, 'foo', '42;43')

    def test_number_and_hash(self):
        with self.assertRaises(ValueError):
            set_cpuset_list(self.d, 'foo', '42#43')

    def test_number_and_dollar(self):
        with self.assertRaises(ValueError):
            set_cpuset_list(self.d, 'foo', '42$43')

    def test_none(self):
        set_cpuset_list(self.d, 'foo', None)
        self.assertEqual(self.d, {})

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            set_cpuset_list(self.d, 'foo', '')

    def test_int(self):
        with self.assertRaises(TypeError):
            set_cpuset_list(self.d, 'foo', 42)

    def test_list(self):
        with self.assertRaises(TypeError):
            set_cpuset_list(self.d, 'foo', ['42'])

    def test_dict(self):
        with self.assertRaises(TypeError):
            set_cpuset_list(self.d, 'foo', {'bar': '42'})

    def test_boolean(self):
        with self.assertRaises(TypeError):
            set_cpuset_list(self.d, 'foo', True)


class set_list_of_ports_tests(ParametersTestCase):

    def test_tcp_port(self):
        with self.assertRaises(TypeError):
            set_list_of_ports(self.d, 'foo', '80/tcp')

    def test_udp_port(self):
        with self.assertRaises(TypeError):
            set_list_of_ports(self.d, 'foo', '13/udp')

    def test_tcp_port(self):
        set_list_of_ports(self.d, 'foo', ['80/tcp'])
        self.assertEqual(self.d, {'foo': ['80/tcp']})

    def test_udp_port(self):
        set_list_of_ports(self.d, 'foo', ['13/udp'])
        self.assertEqual(self.d, {'foo': ['13/udp']})

    def test_list_of_tcp_ports(self):
        set_list_of_ports(self.d, 'foo', ['80/tcp', '443/tcp'])
        self.assertEqual(self.d, {'foo': ['80/tcp', '443/tcp']})

    def test_list_of_udp_ports(self):
        set_list_of_ports(self.d, 'foo', ['11/udp', '13/udp'])
        self.assertEqual(self.d, {'foo': ['11/udp', '13/udp']})

    def test_port_without_protocol(self):
        with self.assertRaises(ValueError):
            set_list_of_ports(self.d, 'foo', ['80'])

    def test_port_0(self):
        with self.assertRaises(ValueError):
            set_list_of_ports(self.d, 'foo', ['0/tcp'])

    def test_port_starting_with_0(self):
        with self.assertRaises(ValueError):
            set_list_of_ports(self.d, 'foo', ['08/tcp'])

    def test_protocol_without_port(self):
        with self.assertRaises(ValueError):
            set_list_of_ports(self.d, 'foo', ['/tcp'])

    def test_none(self):
        set_list_of_ports(self.d, 'foo', None)
        self.assertEqual(self.d, {})

    def test_empty_string(self):
        with self.assertRaises(TypeError):
            set_list_of_ports(self.d, 'foo', '')

    def test_int(self):
        with self.assertRaises(TypeError):
            set_list_of_ports(self.d, 'foo', 42)

    def test_dict(self):
        with self.assertRaises(TypeError):
            set_list_of_ports(self.d, 'foo', {'bar': '42'})

    def test_boolean(self):
        with self.assertRaises(TypeError):
            set_list_of_ports(self.d, 'foo', True)

    def test_list_of_int(self):
        with self.assertRaises(TypeError):
            set_list_of_ports(self.d, 'foo', [42])

    def test_list_of_list(self):
        with self.assertRaises(TypeError):
            set_list_of_ports(self.d, 'foo', [['80/tcp']])

    def test_list_of_boolean(self):
        with self.assertRaises(TypeError):
            set_list_of_ports(self.d, 'foo', [True])
