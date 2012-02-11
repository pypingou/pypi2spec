#-*- coding: utf-8 -*-

#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# (C) 2012 - Pierre-Yves Chibon <pingou@pingoured.fr>

"""
Spec class, handles the read/write of the spec file
"""


import datetime
import os
import re
import sys
from jinja2 import Template
try:
    from pypi2spec import get_logger, get_rpm_tag, Pypi2specError
except ImportError:
    from __init__ import get_logger, get_rpm_tag, Pypi2specError


def format_description(description):
    """ Format the description as required by rpm """
    step = 75
    cnt = 0
    out = []
    char = 0
    while cnt < len(description) and char < description.rfind(" "):
        if len(description[cnt:]) >= step:
            char = description[cnt: cnt + step].rfind(" ") + cnt
            out.append(description[cnt: char])
            cnt = char + 1
        else:
            out.append(description[cnt:])
            cnt += len(description[cnt:])

    return "\n".join(out)


def format_dependencies(dependencies):
    """ Format the dependencies cleanning them as much as possible for rpm.
    """
    ignorelist = ['python']
    # Regular expression used to determine whether the string is a
    # version number
    versionmotif = re.compile('\d\.\d\.?\d?')
    char = {
            '\r': '',
            '(': ' ',
            ')': ' ',
            ',': ' ',
            '  ': ' ',
            }

    for key in char.keys():
        dependencies = dependencies.replace(key, char[key])
    dep_list = []

    for dep in dependencies.split(' '):
        if dep.strip():
            if  not ">" in dep \
            and not "<" in dep \
            and not "=" in dep \
            and len(versionmotif.findall(dep)) == 0 \
            and dep.strip() not in ignorelist:
                dep = dep.strip()
                dep_list.append(dep)

    return ' '.join(dep_list).strip()


class Spec:
    """
    Spec Class
        Write the spec file.
    """

    def __init__(self, settings, package=None):
        """ Constructor.
        """
        self.package = package
        self.settings = settings
        self.__dict = {}
        self.log = get_logger()
        self.spec = None

    def fill_spec_info(self):
        """ Fills the different variable required for the spec file. """
        self.log.info('Filling spec variable from info collected')
        self.__dict['name'] = self.package.name
        self.__dict['arch'] = self.package.arch
        self.__dict['version'] = self.package.version
        self.__dict['summary'] = self.package.summary
        self.__dict['license'] = self.package.license
        self.__dict['description'] = format_description(self.package.description)
        self.__dict['URL'] = self.package.url
        self.__dict['source0'] = self.package.source0
        self.__dict['packager'] = self.settings.get('packager')
        self.__dict['email'] = self.settings.get('email')
        self.__dict['date'] = datetime.datetime.now(
            ).strftime("%a %b %d %Y")

    def get_specfile(self):
        """ Return the path to the spec file.
        """
        specdir = get_rpm_tag('_specdir')
        specname = '%s.spec' % self.package.name
        return '%s/%s' % (specdir, specname)

    def read_specfile(self):
        """ Read the specfile present in the spec directory.
        """
        specfile = self.get_specfile()
        if os.path.exists(specfile) and os.path.isfile(specfile):
            self.log.info('Reading file %s' % specfile)
            try:
                stream = open(specfile, 'r')
                self.spec = stream.read()
                stream.close()
            except IOError, err:
                self.log.info('Cannot read the file %s' % specfile)
                self.log.debug('ERROR: %s' % err)

    def get_template(self):
        """ Read the empty template and fills it with the information
        retrieved.
        """
        template = '%s/specfile.tpl' % os.path.dirname(__file__)
        self.log.info('Filling spec template')
        try:
            stream = open(template, 'r')
            tplfile = stream.read()
            stream.close()
            mytemplate = Template(tplfile)
            self.spec = mytemplate.render(self.__dict)
        except IOError, err:
            self.log.debug('ERROR: %s' % err)
            raise Pypi2specError('Cannot read the file %s' % template)

    def write_spec(self, verbose=False):
        """ Write down the spec to the spec directory as returned by rpm.
        """
        specfile = self.get_specfile()
        self.log.info('Writing file %s' % specfile)
        try:
            stream = open(specfile, 'w')
            stream.write(self.spec)
            stream.close()
            self.log.debug('Spec file writen: %s' % specfile)
            print 'Spec file writen: %s' % specfile
        except IOError, err:
            print 'Cannot write the file %s' % specfile
            self.log.debug('ERROR: %s' % err)
