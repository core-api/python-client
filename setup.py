#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import re
import os
import shutil
import sys


def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    init_py = open(os.path.join(package, '__init__.py')).read()
    return re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)


def get_packages(package):
    """
    Return root package and all sub-packages.
    """
    return [dirpath
            for dirpath, dirnames, filenames in os.walk(package)
            if os.path.exists(os.path.join(dirpath, '__init__.py'))]


def get_package_data(package):
    """
    Return all files under the root package, that are not in a
    package themselves.
    """
    walk = [(dirpath.replace(package + os.sep, '', 1), filenames)
            for dirpath, dirnames, filenames in os.walk(package)
            if not os.path.exists(os.path.join(dirpath, '__init__.py'))]

    filepaths = []
    for base, filenames in walk:
        filepaths.extend([os.path.join(base, filename)
                          for filename in filenames])
    return {package: filepaths}


version = get_version('coreapi')


if sys.argv[-1] == 'publish':
    os.system("python setup.py sdist bdist_wheel upload")
    print("You probably want to also tag the version now:")
    print("  git tag -a %s -m 'version %s'" % (version, version))
    print("  git push --tags")
    sys.exit()


setup(
    name='coreapi',
    version=version,
    url='https://github.com/core-api/python-client',
    license='BSD',
    description='Python client library for Core API.',
    author='Tom Christie',
    author_email='tom@tomchristie.com',
    packages=get_packages('coreapi'),
    package_data=get_package_data('coreapi'),
    install_requires=[
        'coreschema',
        'requests',
        'itypes',
        'uritemplate'
    ],
    entry_points={
        'coreapi.codecs': [
            'corejson=coreapi.codecs:CoreJSONCodec',
            'json=coreapi.codecs:JSONCodec',
            'text=coreapi.codecs:TextCodec',
            'download=coreapi.codecs:DownloadCodec',
        ],
        'coreapi.transports': [
            'http=coreapi.transports:HTTPTransport',
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
