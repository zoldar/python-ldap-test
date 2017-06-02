import sys
import unittest
from os import path

sys.path.insert(0, path.abspath(path.join(path.dirname(__file__), '..', '..')))

import ldap3

from ldap_test import LdapServer


class LdapServerTest(unittest.TestCase):
    def test_default(self):
        server = LdapServer()
        server.start()

        dn = server.config['bind_dn']
        pw = server.config['password']

        srv = ldap3.Server('localhost', port=server.config['port'])
        conn = ldap3.Connection(srv, user=dn, password=pw, auto_bind=True)

        base_dn = server.config['base']['dn']
        search_filter = '(objectclass=domain)'
        attrs = ['dc']

        conn.search(base_dn, search_filter, attributes=attrs)

        self.assertEqual(conn.response, [{
            'dn': 'dc=example,dc=com',
            'raw_attributes': {'dc': [b'example']},
            'attributes': {'dc': ['example']},
            'type': 'searchResEntry'
        }])

        conn.unbind()
        server.stop()

    def test_default_with_delay(self):
        server = LdapServer(java_delay=1)
        server.start()

        dn = server.config['bind_dn']
        pw = server.config['password']

        srv = ldap3.Server('localhost', port=server.config['port'])
        conn = ldap3.Connection(srv, user=dn, password=pw, auto_bind=True)

        base_dn = server.config['base']['dn']
        search_filter = '(objectclass=domain)'
        attrs = ['dc']

        conn.search(base_dn, search_filter, attributes=attrs)

        self.assertEqual(conn.response, [{
            'dn': 'dc=example,dc=com',
            'raw_attributes': {'dc': [b'example']},
            'attributes': {'dc': ['example']},
            'type': 'searchResEntry'
        }])

        conn.unbind()
        server.stop()

    def test_config(self):
        server = LdapServer({
            'port': 3333,
            'bind_dn': 'cn=admin,dc=zoldar,dc=net',
            'password': 'pass1',
            'base': {
                'objectclass': ['domain'],
                'dn': 'dc=zoldar,dc=net',
                'attributes': {'dc': 'zoldar'}
            },
            'entries': [{
                'objectclass': ['domain'],
                'dn': 'dc=users,dc=zoldar,dc=net',
                'attributes': {'dc': 'users'}
            }, {
                'objectclass': ['organization'],
                'dn': 'o=foocompany,dc=users,dc=zoldar,dc=net',
                'attributes': {'o': 'foocompany'}
            }],
        })
        server.start()

        dn = "cn=admin,dc=zoldar,dc=net"
        pw = "pass1"

        srv = ldap3.Server('localhost', port=3333)
        conn = ldap3.Connection(srv, user=dn, password=pw, auto_bind=True)

        base_dn = 'dc=zoldar,dc=net'
        search_filter = '(objectclass=organization)'
        attrs = ['o']

        conn.search(base_dn, search_filter, attributes=attrs)

        self.assertEqual(conn.response, [{
            'dn': 'o=foocompany,dc=users,dc=zoldar,dc=net',
            'raw_attributes': {'o': [b'foocompany']},
            'attributes': {'o': ['foocompany']},
            'type': 'searchResEntry'
        }])

        conn.unbind()
        server.stop()

    def test_non_standard_objects(self):
        server = LdapServer({
            'port': 3333,
            'bind_dn': 'cn=admin,dc=zoldar,dc=net',
            'password': 'pass1',
            'base': {
                'objectclass': ['domain'],
                'dn': 'dc=zoldar,dc=net',
                'attributes': {'dc': 'zoldar'}
            },
            'entries': [{
                'objectclass': ['domain'],
                'dn': 'dc=users,dc=zoldar,dc=net',
                'attributes': {'dc': 'users'}
            }, {
                'objectclass': ['foo'],
                'dn': 'bar=foovar,dc=users,dc=zoldar,dc=net',
                'attributes': {'bar': 'foovar'}
            }],
        })
        server.start()

        dn = "cn=admin,dc=zoldar,dc=net"
        pw = "pass1"

        srv = ldap3.Server('localhost', port=3333)
        conn = ldap3.Connection(srv, user=dn, password=pw, auto_bind=True)

        base_dn = 'dc=zoldar,dc=net'
        search_filter = '(objectclass=foo)'
        attrs = ['bar']

        conn.search(base_dn, search_filter, attributes=attrs)

        self.assertEqual(conn.response, [{
            'dn': 'bar=foovar,dc=users,dc=zoldar,dc=net',
            'raw_attributes': {'bar': [b'foovar']},
            'attributes': {'bar': ['foovar']},
            'type': 'searchResEntry'
        }])

        conn.unbind()
        server.stop()

    def test_multiple_instances(self):
        servers = {}
        for sid in (1, 2):
            domain = 'example{0}'.format(sid)
            servers[sid] = LdapServer({
                'port': 10389 + (sid * 1000),
                'bind_dn': 'cn=admin,dc={0},dc=com'.format(domain),
                'base': {
                    'objectclass': ['domain'],
                    'dn': 'dc={0},dc=com'.format(domain),
                    'attributes': {'dc': domain}
                },
            })
            servers[sid].start()

        search_filter = '(objectclass=domain)'
        attrs = ['dc']

        # server1
        dn = servers[1].config['bind_dn']
        pw = servers[1].config['password']
        base_dn = servers[1].config['base']['dn']
        port = servers[1].config['port']

        srv = ldap3.Server('localhost', port=port)
        conn = ldap3.Connection(srv, user=dn, password=pw, auto_bind=True)
        conn.search(base_dn, search_filter, attributes=attrs)

        self.assertEqual(conn.response, [{
            'dn': 'dc=example1,dc=com',
            'raw_attributes': {'dc': [b'example1']},
            'attributes': {'dc': ['example1']},
            'type': 'searchResEntry'
        }])

        conn.unbind()

        # server2
        dn = servers[2].config['bind_dn']
        pw = servers[2].config['password']
        base_dn = servers[2].config['base']['dn']
        port = servers[2].config['port']

        srv = ldap3.Server('localhost', port=port)
        conn = ldap3.Connection(srv, user=dn, password=pw, auto_bind=True)
        conn.search(base_dn, search_filter, attributes=attrs)

        self.assertEqual(conn.response, [{
            'dn': 'dc=example2,dc=com',
            'raw_attributes': {'dc': [b'example2']},
            'attributes': {'dc': ['example2']},
            'type': 'searchResEntry'
        }])

        conn.unbind()

        for server in servers.values():
            server.stop()


if __name__ == '__main__':
    unittest.main()
