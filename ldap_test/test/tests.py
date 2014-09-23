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

        server.stop()

if __name__ == '__main__':
    unittest.main()
