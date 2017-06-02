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

    import ldap3

    from ldap_test import LdapServer

    server = LdapServer()

    try:
        server.start()

        dn = server.config['bind_dn']
        pw = server.config['password']

        srv = ldap3.Server('localhost', port=server.config['port'])
        conn = ldap3.Connection(srv, user=dn, password=pw, auto_bind=True)

        base_dn = server.config['base']['dn']
        search_filter = '(objectclass=domain)'
        attrs = ['dc']

        conn.search(base_dn, search_filter, attributes=attrs)

        print conn.response
        # [{
        #    'dn': 'dc=example,dc=com',
        #    'raw_attributes': {'dc': [b'example']},
        #    'attributes': {'dc': ['example']},
        #    'type': 'searchResEntry'
        # }]
    finally:
        server.stop()

Another example with non-standard settings:

    import ldap3

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

        srv = ldap3.Server('localhost', port=3333)
        conn = ldap3.Connection(srv, user=dn, password=pw, auto_bind=True)

        base_dn = 'dc=zoldar,dc=net'
        search_filter = '(objectclass=organization)'
        attrs = ['o']

        conn.search(base_dn, search_filter, attributes=attrs)

        print conn.response
        # [{
        #    'dn': 'o=foocompany,dc=users,dc=zoldar,dc=net',
        #    'raw_attributes': {'o': [b'foocompany']},
        #    'attributes': {'o': ['foocompany']},
        #    'type': 'searchResEntry'
        # }]
    finally:
        server.stop()

And, finally, an example of running multiple LDAP servers:

    import ldap3

    from ldap_test import LdapServer

    servers = {}

    try:
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

        print conn.response
        # [{
        #    'dn': 'dc=example1,dc=com',
        #    'raw_attributes': {'dc': [b'example1']},
        #    'attributes': {'dc': ['example1']},
        #    'type': 'searchResEntry'
        # }]

        conn.unbind()

        # server2
        dn = servers[2].config['bind_dn']
        pw = servers[2].config['password']
        base_dn = servers[2].config['base']['dn']
        port = servers[2].config['port']

        srv = ldap3.Server('localhost', port=port)
        conn = ldap3.Connection(srv, user=dn, password=pw, auto_bind=True)
        conn.search(base_dn, search_filter, attributes=attrs)

        print conn.response
        # [{
        #    'dn': 'dc=example2,dc=com',
        #    'raw_attributes': {'dc': [b'example2']},
        #    'attributes': {'dc': ['example2']},
        #    'type': 'searchResEntry'
        # }]

        conn.unbind()
    finally:
        for server in servers.values():
            server.stop()

The initial server configuration is represented by a simple dict, which may
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
    
## MacOS
For some reason, while running on MacOS, you can experience problems if the JVM doesn't start quickly enough for the py4j gateway to connect, and it goes into an infinite hang.

If you're experiencing this problem, you can set an interval between the JVM startup and the py4j gateway by passing 'java_delay=n' to LdapServer() where 'n' is the number of seconds to wait.  Typically a wait of even 1 second is enough for java to spin up and be ready for the gateway.

To be clear, the following:

    server = LdapServer(config={...}, java_delay=1)
    
will cause a 1 second delay between starting the JVM and creating the py4j gateway, and all should be well.  

In tests, a delay of even 0.5 seconds can be enough, though 0.1 seconds is not.  The exact cause of this problem is unknown.  More information on this 'feature' while running on a Mac is welcome.

## Running Java gateway and proxy on non-standard ports

When there's a necessity to run proxy and gateway on ports different from the default ones
(25333 for Java gateway and 25334 for proxy), the `LdapServer` may be instantiated with
custom ones, passed explicitly to the constructor:

```
server = LdapServer({...}, java_gateway_port=26333, python_proxy_port=26334)
```

This can be useful when several test runs are done in parallel on a single system.

## Reporting issues

Any issues (be it bugs, feature requests or anything else) can be reported through project's [GitHub issues page](https://github.com/zoldar/python-ldap-test/issues).

## Contributors

- John Kristensen ([https://github.com/jerrykan](https://github.com/jerrykan))
- Kevin Rasmussen ([https://github.com/krasmussen](https://github.com/krasmussen))
- Pedro Algarvio ([https://github.com/s0undt3ch](https://github.com/s0undt3ch))
- Nik Ogura ([https://github.com/nikogura])(https://github.com/nikogura)

## License

Copyright © 2016 Adrian Gruntkowski

Distributed under the MIT License.
