#!/bin/bash

if [ "$1" == "prod" ]; then
    PYPI=pypi
elif [ "$1" == "test" ]; then
    PYPI=pypitest
else
    echo "Usage: $0 prod|test"
    exit 1
fi

pandoc -f markdown -t rst README.md > README.txt

python setup.py register -r $PYPI

python setup.py sdist upload -r $PYPI

rm README.txt
