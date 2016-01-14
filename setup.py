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

setup(
    name='chembl_api',
    version='0.5.16',
    author='Michal Nowotka',
    author_email='mnowotka@ebi.ac.uk',
    description='Python package providing RESTful chembl API.',
    url='https://www.ebi.ac.uk/chembldb/index.php/ws',
    license='Apache Software License',
    packages=['chembl_api'],
    long_description=open('README.rst').read(),
    install_requires=[
        'Django==1.5.5',
        'simplejson==2.3.2',
        'defusedxml>=0.4.1',
        'django-tastypie==0.10',
        'chembl_business_model>=0.5.3'
    ],
    include_package_data=False,
    classifiers=['Development Status :: 2 - Pre-Alpha',
                 'Environment :: Web Environment',
                 'Framework :: Django',
                 'Intended Audience :: Developers',
                 'License :: OSI Approved :: Apache Software License',
                 'Operating System :: POSIX :: Linux',
                 'Programming Language :: Python :: 2.7',
                 'Topic :: Scientific/Engineering :: Chemistry'],
    zip_safe=False,
)
