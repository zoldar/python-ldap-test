from distutils.core import setup
from setuptools.command.install import install


try:
    description = open('README.txt').read()
except:
    description = open('README.md').read()


setup(
    name='python-ldap-test',
    version='0.0.8',
    author='Adrian Gruntkowski',
    author_email='adrian.gruntkowski@gmail.com',
    packages=['ldap_test', 'ldap_test.test'],
    url='https://github.com/zoldar/python-ldap-test/',
    license='LICENSE.txt',
    description=('Tool for testing code speaking with LDAP server. Allows to easily'
                 ' configure and run an embedded, in-memory LDAP server. Uses'
                 ' UnboundID LDAP SDK through Py4J.'),
    keywords = ['testing', 'tests', 'test', 'ldap'],
    long_description=description,
    install_requires=[
        "py4j >= 0.8",
    ],
    package_data={
        '': ['*.txt'],
        'ldap_test': ['*.jar'],
    }
)
