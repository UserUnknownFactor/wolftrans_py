"""
WolfRPG game file translations unpack/repack tool
-----------

Unpacks internal WolfRPG game files to a translation scripts and repacks those scripts back. Needs a separate tool for unpacking/repacking the .wolf files themselves.

Link
`````
 `github <https://github.com/UserUnknownFactor/wolftrans_py>`_


"""
from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md')) as f: long_description = f.read()
with open(path.join(this_directory, 'requirements.txt')) as f: requirements = f.read().splitlines()

setup(
    name='wolftrans',
    version='0.4.0',
    url='https://github.com/UserUnknownFactor/wolftrans_py',
    license='MIT',
    author='UserUnknownFactor',
    author_email='noreply@example.com',
    description='Unpacks and repacks translatable strings of WolfRPG games',
    long_description=long_description,
    install_requires=requirements,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Games/Entertainment',
    ],
    packages = find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': ['wolf_unpack=wolfrpg.extract:main','wolf_repack=wolfrpg.repack:main',]
    }
)
