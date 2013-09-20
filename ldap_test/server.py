#!/usr/bin/env python

import logging
import os
import subprocess
import atexit
import sys
from distutils.spawn import find_executable

from py4j.java_gateway import JavaGateway, GatewayClient, GatewayConnection
from py4j.protocol import Py4JNetworkError


CONFIG_PARAMS = ('port', 'base', 'entries', 'ldifs', 'bind_dn', 'password')
DEFAULT_CONFIG = {
    'port': 10389,
    'bind_dn': 'cn=admin,dc=example,dc=com',
    'password': 'password',
    'base': {'objectclass': ['domain'],
             'dn': 'dc=example,dc=com',
             'attributes': {'dc': 'example'}}
}

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
JVM_SERVER_BIN = os.path.join(
    PACKAGE_DIR,
    "ldap-test-server-0.0.2-SNAPSHOT-jar-with-dependencies.jar")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('ldap_test')

SERVER_PROCESS = None
JVM_GATEWAY = None


def server_cleanup():
    global SERVER_PROCESS, JVM_GATEWAY
    if JVM_GATEWAY:
        JVM_GATEWAY.shutdown()
    if SERVER_PROCESS:
        SERVER_PROCESS.kill()


atexit.register(server_cleanup)


def run_jvm_gateway():
    try:
        return JavaGateway(gateway_client=SlowGatewayClient(), eager_load=True)
    except Py4JNetworkError:
        log.error("Failed to connect!")
        raise


def run_jvm_server():
    if not os.path.isfile(JVM_SERVER_BIN):
        raise Exception("%s is missing!" % (JVM_SERVER_BIN,))

    try:
        return subprocess.Popen("exec %s -jar %s" % (
            find_executable("java"),
            JVM_SERVER_BIN), shell=True)
    except OSError, e:
        log.error("Failed to run JVM server because: %s" % (e,))
        raise


class SlowGatewayClient(GatewayClient):
    def _create_connection(self):
        connection = MuffledGatewayConnection(self.address, self.port,
                            self.auto_close, self.gateway_property)
        while True:
            connection_success = False
            try:
                connection.start()
                connection_success = True
            except Py4JNetworkError:
                pass
            if connection_success:
                break
        return connection


class MuffledGatewayConnection(GatewayConnection):
    def start(self):
        try:
            self.socket.connect((self.address, self.port))
            self.is_connected = True
            self.stream = self.socket.makefile('rb', 0)
        except Exception:
            msg = 'An error occurred while trying to connect to the Java '\
                            'server'
            raise Py4JNetworkError(msg)


class ConfigBuilder(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.builder = self.gateway.jvm.net.zoldar.ldap.testserver.LdapBuilder

    def build_from(self, config_map=None):
        config_map = config_map or {}
        config_map = dict(DEFAULT_CONFIG, **config_map)
        config = self.builder.config()

        for param in CONFIG_PARAMS:
            if param in config_map:
                getattr(self, "_set_%s" % (param,))(config, config_map[param])

        return config_map, config.build()

    def _set_port(self, config, port):
        config.port(port)

    def _set_base(self, config, entry_map):
        config.base(self._map_to_entry(entry_map))

    def _set_entries(self, config, entries):
        config.entries(self._list_to_array(
            self.gateway.jvm.com.github
                .trevershick.test.ldap.annotations.LdapEntry,
            [self._map_to_entry(x) for x in entries]
        ))

    def _set_ldifs(self, config, ldifs):
        config.ldifs(self._list_to_array(
            self.gateway.jvm.com.github.trevershick.test.ldap.annotations.Ldif,
            [self.builder.ldif(x) for x in ldifs]
        ))

    def _set_bind_dn(self, config, bind_dn):
        config.bindDn(bind_dn)

    def _set_password(self, config, password):
        config.password(password)

    def _map_to_entry(self, entry):
        dn = entry['dn']
        objectclass = entry['objectclass']
        attributes = entry.get('attributes') or {}

        if isinstance(objectclass, basestring):
            objectclass = [objectclass]

        attr_objects = []
        for attr_name in attributes:
            value = attributes[attr_name]
            if isinstance(value, basestring):
                value = [value]
            attr_objects.append(self.builder.attribute(
                attr_name,
                self._list_to_array(self.gateway.jvm.String, value)
            ))

        return self.builder.entry(
            dn,
            self._list_to_array(self.gateway.jvm.String, objectclass),
            self._list_to_array(
                self.gateway.jvm.com.github
                    .trevershick.test.ldap.annotations.LdapAttribute,
                attr_objects)
        )

    def _list_to_array(self, value_type, lst):
        array = self.gateway.new_array(value_type, len(lst))
        for idx, value in enumerate(lst):
            array[idx] = value
        return array


class LdapServer(object):
    def __init__(self, config=None):
        global SERVER_PROCESS, JVM_GATEWAY

        if SERVER_PROCESS is None:
            SERVER_PROCESS = run_jvm_server()

        if JVM_GATEWAY is None:
            JVM_GATEWAY = run_jvm_gateway()

        self.gateway = JVM_GATEWAY
        self.server = self.gateway.entry_point
        self.config, self.config_obj = ConfigBuilder(
            self.gateway
        ).build_from(config)

    def start(self):
        self.server.start(self.config_obj)

    def stop(self):
        self.server.stop()
