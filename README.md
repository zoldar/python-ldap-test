# python-ldap-test

Tool for testing code speaking with LDAP server. Allows to easily configure and run 
an embedded, in-memory LDAP server. Uses UnboundID LDAP SDK through Py4J.
Requires Java runtime on the system path to run the server.

## Installation

With `pip`:

    pip install python-ldap-test


When installing from source:

    git clone https://github.com/zoldar/python-ldap-test
    cd python-ldap-test
    python setup.py install # you may need root privileges if installing system-wide

## Usage

Example library usage with Python ldap client.

    from ldap_test import LdapServer

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

Another example with non-standard settings:

    from ldap_test import LdapServer

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

The server initial configuration is represented by a simple dict, which may
contain one or more optional parameters:

- `port` - a port on which the LDAP server will listen
- `bind_dn` - bind DN entry for authentication
- `password` - authentication password
- `base` - base DN entry
- `entries` - a list of dicts representing intially loaded entries 
   in the database. `attributes` are optional here
- `ldifs` - a list of strings representing file paths to the LDIF files to load
  on start, like `..., 'ldifs': ['path/to/file1.ldif', 'path/to/file2.ldif'], ...`

The format of entry in `entries` as well as `base` is following:

    {'dn': 'o=some,dc=example,dc=com', # DN identifying the entry
     'objectclass': ['top', 'organization'], # objectclass may be either a 
                                             # string in case of a single 
                                             # class or a list of classes
     'attributes': {        # attributes are optional
        'o': 'some'         # every attribute may have either a single value
                            # or multiple values in a list like
                            # 'ou': ['Value1', 'Value2', ...]
     }
    }

## Reporting issues

Any issues (be it bugs, feature requests or anything else) can be reported through project's [GitHub issues page](https://github.com/zoldar/python-ldap-test/issues).

## License

Copyright © 2013 Adrian Gruntkowski

Distributed under the MIT License.
