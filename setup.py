#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'mnowotka'

import sys

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

if sys.version_info < (2, 7, 3) or sys.version_info >= (2, 7, 7):
    raise Exception('ChEMBL software stack requires python 2.7.3 - 2.7.7')

setup(
    name='chembl-api',
    version='0.9.5',
    author='Michal Nowotka',
    author_email='mnowotka@ebi.ac.uk',
    description='Python package providing RESTful chembl API.',
    url='https://www.ebi.ac.uk/chembldb/index.php/ws',
    license='CC BY-SA 3.0',
    packages=['chembl_api'],
    long_description=open('README.rst').read(),
    install_requires=[
        'Django==1.9.12',
        'simplejson==2.3.2',
        'defusedxml>=0.4.1',
        'django-tastypie==0.13.3',
        'chembl-business-model>=0.9.5'
    ],
    include_package_data=False,
    classifiers=['Development Status :: 2 - Pre-Alpha',
                 'Environment :: Web Environment',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: Creative Commons :: Attribution-ShareAlike 3.0 Unported',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python :: 2.7',
                 'Topic :: Scientific/Engineering :: Chemistry'],
    zip_safe=False,
)
