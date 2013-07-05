#!/usr/bin/env python

import ldap
import sys

from ldap_test import LdapServer


if __name__ == "__main__":

    server = LdapServer()

    try:
        server.start()

        dn = server.config['bind_dn']
        pw = server.config['password']

        con = ldap.initialize('ldap://localhost:%s' % (server.config['port'],))
        con.simple_bind_s(dn, pw)

        base_dn = server.config['base']['dn']
        filter = '(objectclass=domain)'
        attrs = ['dc']

        print con.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)

    finally:
        server.stop()

    server = LdapServer({
        'port': 3333,
        'bind_dn': 'cn=admin,dc=zoldar,dc=net',
        'password': 'pass1',
        'base': {'objectclass': ['domain'],
                 'dn': 'dc=zoldar,dc=net',
                 'attributes': {'dc': 'zoldar'}},
        'entries': [
            {'objectclass': 'domain',
             'dn': 'dc=users,dc=zoldar,dc=net',
             'attributes': {'dc': 'users'}},
            {'objectclass': 'organization',
             'dn': 'o=foocompany,dc=users,dc=zoldar,dc=net',
             'attributes': {'o': 'foocompany'}},
        ]
    })

    try:
        server.start()

        dn = "cn=admin,dc=zoldar,dc=net"
        pw = "pass1"

        con = ldap.initialize('ldap://localhost:3333')
        con.simple_bind_s(dn, pw)

        base_dn = 'dc=zoldar,dc=net'
        filter = '(objectclass=domain)'
        attrs = ['o']

        print con.search_s(base_dn, ldap.SCOPE_SUBTREE, filter, attrs)

    finally:
        server.stop()
