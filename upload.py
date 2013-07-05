import pandoc
import os

pandoc.core.PANDOC_PATH = '/usr/bin/pandoc'

doc = pandoc.Document()
doc.markdown = open('README.md').read()

with open('README.txt', 'w+') as fp:
    fp.write(doc.rst)

os.system('python setup.py sdist upload')

os.remove('README.txt')
