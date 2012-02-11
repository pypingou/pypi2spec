#!/usr/bin/env python
import sys
import re

from distutils.core import setup
from src.pypi2spec import __version__

setup(
    name = 'pypi2spec',
    version = __version__,
    description = "Small library to help you generate spec file for pypi project.",
    author = "Pierre-Yves Chibon",
    author_email = "pingou@pingoured.fr",
    maintainer = "Pierre-Yves Chibon",
    maintainer_email = "pingou@pingoured.fr",
    url = "http://github.com/pypingou/pypi2spec",
    license = "GPLv3+",
    long_description = 'pypi2spec makes you life easier at packaging pypi project for Fedora',
    download_url = "http://github.com/pypingou/pypi2spec-%s.tar.gz" % __version__,
	 package_dir = {'pypi2spec': 'src/pypi2spec'},
    packages = ['pypi2spec'],
	 scripts=['pypi2spec'],
)

