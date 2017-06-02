import codecs
from distutils.core import setup


def read(fname):
    '''
    Read a file from the directory where setup.py resides
    '''
    with codecs.open(fname, encoding='utf-8') as rfh:
        return rfh.read()

try:
    description = read('README.txt')
except:
    description = read('README.md')


setup(
    name='python-ldap-test',
    version='0.3.1',
    author='Adrian Gruntkowski',
    author_email='adrian.gruntkowski@gmail.com',
    packages=['ldap_test', 'ldap_test.test'],
    url='https://github.com/zoldar/python-ldap-test/',
    license='LICENSE.txt',
    description=('Tool for testing code speaking with LDAP server. Allows to easily'
                 ' configure and run an embedded, in-memory LDAP server. Uses'
                 ' UnboundID LDAP SDK through Py4J.'),
    keywords=['testing', 'tests', 'test', 'ldap'],
    long_description=description,
    install_requires=[
        "py4j >= 0.10.2.1",
    ],
    package_data={
        '': ['*.txt'],
        'ldap_test': ['*.jar'],
    },
    options={
        'bdist_rpm': {
            'build_requires':[
                'python',
                'python-setuptools',
                'py4j',
            ],
            'requires':[
                'python',
                'py4j',
            ],
        },
    },
)
