# coding:utf-8

import sys
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.version_info < (2, 6):
    error = 'ERROR: petaexpress-sdk requires Python Version 2.6 or above.'
    print >> sys.stderr, error
    sys.exit(1)


setup(
    name='petaexpress-sdk',
    version='1.2.15',
    description='Software Development Kit for PetaExpress Cloud.',
    long_description=open('README.rst', 'rb').read().decode('utf-8'),
    keywords='petaexpress iaas qingstor sdk',
    author='RAKSmart Team',
    author_email='dev@raksmart.com',
    url='https://docs.petaexpress.com/sdk/',
    packages=['petaexpress', 'petaexpress.conn', 'petaexpress.iaas', 'petaexpress.iaas.actions',
              'petaexpress.misc', 'petaexpress.qingstor'],
    package_dir={'petaexpress-sdk': 'petaexpress'},
    namespace_packages=['petaexpress'],
    include_package_data=True,
    install_requires=['future']
)
