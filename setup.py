from distutils.core import setup
from setuptools.command.install import install


setup(
    name='python-ldap-test',
    version='0.0.1',
    author='Adrian Gruntkowski',
    author_email='adrian.gruntkowski@gmail.com',
    packages=['ldap_test', 'ldap_test.test'],
    url='http://pypi.python.org/pypi/python-ldap-test/',
    license='LICENSE.txt',
    description=('Tool for testing code speaking with LDAP. Allows to easily'
                 ' configure and run an embedded, in-memory LDAP server. Uses'
                 ' UnboundID LDAP SDK through Py4J.'),
    long_description=open('README.txt').read(),
    install_requires=[
        "py4j >= 0.8",
    ],
    package_data={
        '': ['*.txt'],
        'ldap_test': ['*.jar'],
    }
)
