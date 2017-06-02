#!/usr/bin/env python

import logging
import os
import time
import subprocess
import atexit
from distutils.spawn import find_executable

from py4j.java_gateway import JavaGateway, GatewayClient, GatewayConnection, GatewayParameters
from py4j.protocol import Py4JNetworkError

try:
    basestring
except NameError:
    basestring = (str, bytes)


CONFIG_PARAMS = ('port', 'base', 'entries', 'ldifs', 'bind_dn', 'password')
DEFAULT_CONFIG = {
    'port': 10389,
    'bind_dn': 'cn=admin,dc=example,dc=com',
    'password': 'password',
    'base': {'objectclass': ['domain'],
             'dn': 'dc=example,dc=com',
             'attributes': {'dc': 'example'}}
}

DEFAULT_GATEWAY_PORT = 25333
DEFAULT_PYTHON_PROXY_PORT = 25334
PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
JVM_SERVER_BIN = os.path.join(
    PACKAGE_DIR,
    "ldap-test-server-0.0.4-SNAPSHOT-jar-with-dependencies.jar")

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


def run_jvm_gateway(gateway_port=DEFAULT_GATEWAY_PORT,
                    python_proxy_port=DEFAULT_PYTHON_PROXY_PORT):
    try:
        log.info('Starting the JavaGateway on python_proxy_port %s', python_proxy_port)
        return JavaGateway(gateway_client=SlowGatewayClient(port=gateway_port),
                           python_proxy_port=python_proxy_port)
    except Py4JNetworkError:
        log.error("Failed to connect!")
        raise


def run_jvm_server(gateway_port=DEFAULT_GATEWAY_PORT):
    if not os.path.isfile(JVM_SERVER_BIN):
        raise Exception("%s is missing!" % (JVM_SERVER_BIN,))

    jre_executable = find_executable("java")

    if jre_executable is None:
        raise Exception("'java' executable not found in system path!")

    try:
        return subprocess.Popen("exec %s -jar %s --port %s" % (
            jre_executable,
            JVM_SERVER_BIN,
            gateway_port), shell=True)
    except OSError as e:
        log.error("Failed to run JVM server because: %s" % (e,))
        raise


class SlowGatewayClient(GatewayClient):
    def _create_connection(self):
        while True:
            parameters = GatewayParameters(address=self.address,
                                           port=self.port,
                                           auto_close=self.auto_close,
                                           eager_load=True)
            connection = MuffledGatewayConnection(parameters, self.gateway_property)
            connection_success = False
            try:
                connection.start()
                connection_success = True
            except Py4JNetworkError:
                pass
            except (KeyboardInterrupt, SystemExit):
                break
            if connection_success:
                break
            time.sleep(0.1)
        return connection


class MuffledGatewayConnection(GatewayConnection):
    def start(self):
        try:
            log.debug('%s is trying to connect to %s:%d', self.__class__.__name__, self.address, self.port)
            self.socket.connect((self.address, self.port))
            self.is_connected = True
            self.stream = self.socket.makefile('rb', 0)
            log.debug('%s is now connected to the Java server', self.__class__.__name__)
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
    def __init__(self, config=None,
                 java_gateway_port=DEFAULT_GATEWAY_PORT,
                 python_proxy_port=DEFAULT_PYTHON_PROXY_PORT, java_delay=None):
        global SERVER_PROCESS, JVM_GATEWAY

        if SERVER_PROCESS is None:
            SERVER_PROCESS = run_jvm_server(java_gateway_port)

        # Added to introduce a delay between starting the SERVER_PROCESS and the JVM_GATEWAY if desired.
        # This seems to be a problem on some MacOS systems, and without it you end up with an infinite hang.
        if java_delay:
            time.sleep(java_delay)

        if JVM_GATEWAY is None:
            JVM_GATEWAY = run_jvm_gateway(java_gateway_port, python_proxy_port)

        self.server = JVM_GATEWAY.entry_point
        self.config, self._config_obj = \
            ConfigBuilder(JVM_GATEWAY).build_from(config)
        self.server_id = self.server.create(self._config_obj)

    def start(self):
        self.server.start(self.server_id)

    def stop(self):
        self.server.stop(self.server_id)
