#!/bin/bash

if [ "$1" == "prod" ]; then
    PYPI=pypi
elif [ "$1" == "test" ]; then
    PYPI=pypitest
else
    echo "Usage: $0 prod|test"
    exit 1
fi

/usr/bin/pandoc -f markdown -t rst README.md > README.txt

/usr/bin/python setup.py register -r $PYPI

/usr/bin/python setup.py sdist upload -r $PYPI

/bin/rm README.txt
