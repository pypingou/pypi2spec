#!/usr/bin/env python
import sys
import re

from setuptools import setup
from pypi2spec import __version__

description = "Small library to help you generate spec file for pypi project."

long_description = """
pypi2spec makes you life easier at packaging pypi project for Fedora.
"""

download_url = "http://github.com/pypingou/pypi2spec-%s.tar.gz" % __version__

requirements = [
    'rdflib',
    'jinja2',
]

try:
    import argparse
except ImportError:
    requirements.append('argparse')

setup(
    name='pypi2spec',
    version=__version__,
    description=description,
    author="Pierre-Yves Chibon",
    author_email="pingou@pingoured.fr",
    maintainer="Pierre-Yves Chibon",
    maintainer_email="pingou@pingoured.fr",
    url="http://github.com/pypingou/pypi2spec",
    license="GPLv3+",
    long_description=long_description,
    download_url=download_url,
    packages=['pypi2spec'],
    include_package_data=True,
    install_requires=requirements,
    entry_points="""
    [console_scripts]
    pypi2spec = pypi2spec:main
    """
)
