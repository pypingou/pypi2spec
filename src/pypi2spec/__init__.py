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


import argparse
import ConfigParser
import logging
import rdflib
import shutil
import tarfile
import os
import urllib2

from rdflib import Namespace, BNode
from subprocess import Popen, PIPE
from tarfile import TarError

logging.basicConfig()
LOG = logging.getLogger('Pypi2spec')
LOG.setLevel('DEBUG')
__version__ = '0.1.0'


def create_conf(configfile):
    """Check if the provided configuration file exists, generate the
    folder if it does not and return True or False according to the
    initial check.

    :arg configfile, name of the configuration file looked for.
    """
    if not os.path.exists(configfile):
        dirn = os.path.dirname(configfile)
        if not os.path.exists(dirn):
            os.makedirs(dirn)
        return True
    return False


def save_config(configfile, parser):
    """"Save the configuration into the specified file.

    :arg configfile, name of the file in which to write the configuration
    :arg parser, ConfigParser object containing the configuration to
    write down.
    """
    conf = open(configfile, 'w')
    parser.write(conf)
    conf.close()

def get_logger():
    """ Return the logger. """
    return LOG


def get_rpm_tag(tag):
    """" Reads the .rpmmacros and set the values accordingly
    Code from José Matos.
    :arg tag, the rpm tag to find the value of
    """
    dirname = Popen(["rpm", "-E", '%' + tag], stdout=PIPE).stdout.read()[:-1]
    return dirname


def move_sources(fullpath, sources):
    """ Copy the tarball from its current location to the sourcedir as
    defined by rpm.

    :arg fullpath, the fullpath to the sources in their current location.
    :arg sources, the name of the file in which the origin will be copied.
    """
    sourcedir = get_rpm_tag('_sourcedir')
    dest = '%s/%s' % (sourcedir, sources)
    shutil.copyfile(fullpath, dest)


class Settings(object):
    """ Pypi2spec user config Setting"""
    # Editor to use in the spec
    packager = os.getlogin()
    # Editor email to use in the spec
    email = ''

    def __init__(self):
        """Constructor of the Settings object.
        This instanciate the Settings object and load into the _dict
        attributes the default configuration which each available option.
        """
        self._dict = {
                        'packager': self.packager,
                        'email': self.email,
                    }
        self.load_config('.config/pypi2spec', 'main')

    def load_config(self, configfile, sec):
        """Load the configuration in memory.

        :arg configfile, name of the configuration file loaded.
        :arg sec, section of the configuration retrieved.
        """
        parser = ConfigParser.ConfigParser()
        configfile = os.environ['HOME'] + "/" + configfile
        is_new = create_conf(configfile)
        parser.read(configfile)
        if not parser.has_section(sec):
            parser.add_section(sec)
        self.populate(parser, sec)
        if is_new:
            save_config(configfile, parser)

    def set(self, key, value):
        """ Set the value to the given key in the settings.

        :arg key, name of the parameter to set from the settings.
        :arg value, value of the parameter to set from the settings.
        """
        if not key in self._dict.keys():
            raise KeyError(key)
        self._dict[key] = value

    def get(self, key):
        """ Return the associated with the given key in the settings.

        :arg key, name of the parameter to retrieve from the settings.
        """
        if not key in self._dict.keys():
            raise KeyError(key)
        return self._dict[key]

    def populate(self, parser, section):
        """"Set option values from a INI file section.

        :arg parser: ConfigParser instance (or subclass)
        :arg section: INI file section to read use.
        """
        if parser.has_section(section):
            opts = set(parser.options(section))
        else:
            opts = set()

        for name in self._dict.iterkeys():
            value = None
            if name in opts:
                value = parser.get(section, name)
                parser.set(section, name, value)
                self._dict[name] = value
            else:
                parser.set(section, name, self._dict[name])

class Pypi2specError(Exception):
    """ Pypi2specError class
    Template for all the error of the project
    """

    def __init__(self, value):
        """ Constructor. """
        self.value = value

    def __str__(self):
        """ Represent the error. """
        return str(self.value)


class Pypi2spec(object):
    """ Pypi2spec main class whose goal is to get the all the info
    needed for the spec file.
    """

    def __init__(self, name):
        """ Constructor.
        :arg name, the name of the library on the pypi website.
        """
        self.name = name
        self.log = get_logger()
        self.version = ''
        self.summary = ''
        self.license = ''
        self.url = 'http://pypi.python.org/pypi/%s' % name
        self.source0 = ''
        self.source = ''
        self.arch = False

    def determine_arch(self):
        """ Determine if the package is arch or noarch by looking at the
        sources.
        Set arch to True if the package is arch dependant.
        Set arch to False if the package is noarch.
        Let arch to None if could not determine.
        """
        self.log.info('Determining if the package is arch dependant or not')
        extensions = ['c', 'C', 'cp', 'cpp', 'h', 'H',]
        if os.path.exists(self.name):
            for root, dirs, files in os.walk(self.name):
                for entry in files:
                    if '.' in entry:
                        extension = entry.rsplit('.', 1)[1]
                        if extension in extensions \
                                or 'f' in extension \
                                or 'F' in extension:
                            self.arch = True
                            self.log.info('Package is arch dependant')
                            return
            self.arch = False
            self.log.info('Package is not arch dependant')
            return
        else:
            self.log.info(
                'Could not find the extracted source to search the arch')

    def download(self, force=False):
        """ Download the source of the package into the source directory
        which we retrieve from rpm directly.

        arg force, boolean whether to force the download of the sources
        even if they are on the system already.
        """
        sourcedir = get_rpm_tag('_sourcedir')
        sources = '%s/%s' % (sourcedir, self.source)

        if not force and os.path.exists(sources) and os.path.isfile(sources):
            self.log.info(
                "Sources are already present, no need to re-download")
            return

        url = self.source0.rsplit('/', 1)[0]
        url = '{url}/{source}'.format(url=url, source=self.source)
        self.log.info('Downloading %s' % url)

        remotefile = urllib2.urlopen(url)
        localfile = open(sources, 'w')
        localfile.write(remotefile.read())
        localfile.close()

    def extract_sources(self):
        """ Extract the sources into the current directory. """
        sourcedir = get_rpm_tag('_sourcedir')
        tarball = "%s/%s" % (sourcedir, self.source)
        self.log.info("Opening: %s" % tarball)
        try:
            tar = tarfile.open(tarball)
            tar.extractall()
            tar.close()
        except TarError, err:
            self.log.debug("Error while extracting the tarball")
            self.log.debug("ERROR: %s" % err)

    def remove_sources(self):
        """ Remove the source we extracted in the current working
        directory.
        """
        source = '%s-%s' % (self.name, self.version)
        self.log.info('Removing extracted sources: "%s"' % source)
        try:
            shutil.rmtree(source)
        except (IOError, OSError), err:
            self.log.info('Could not remove the extracted sources: "%s"'\
                % source)
            self.log.debug('ERROR: %s' % err)

    def retrieve_info(self):
        """ Retrieve all the information from pypi to fill up the spec
        file.
        """
        g = rdflib.Graph()
        try:
            g.parse('http://pypi.python.org/pypi?:action=doap&name=%s' % \
                self.name, format='xml')
        except urllib2.HTTPError, err:
            self.log.debug('ERROR while downloading the doap file:\n  %s'
                % err)
            raise Pypi2specError('Could not retrieve information for the'
                'project "%s". Did you make a typo?' % self.name)
        DOAP = Namespace('http://usefulinc.com/ns/doap#')
        RDFS = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        version_node = g.value(predicate=RDFS['type'],
            object=DOAP['Version'])
        self.version = g.value(subject=version_node,
            predicate=DOAP['revision'])
        project_node = g.value(predicate=RDFS['type'],
            object=DOAP['Project'])
        self.summary = g.value(subject=project_node,
            predicate=DOAP['shortdesc'])
        self.description = g.value(subject=project_node,
            predicate=DOAP['description'])
        self.source0 = 'http://pypi.python.org/packages/source/p/%s/%s-%s.tar.gz' % \
        (self.name, self.name, self.version)
        self.source = '%s-%s.tar.gz' % (self.name, self.version)

class Pypi2specUI(object):
    """ Class handling the user interface. """

    def setup_parser(self):
        """ Command line parser. """
        self.parser = argparse.ArgumentParser(usage='%(prog)s [options]',
                prog='pypi2spec')
        self.parser.add_argument('--version', action='version',
            version='%(prog)s ' + __version__)
        self.parser.add_argument('package',
            help='Name of the pypi library to package.')
        self.parser.add_argument('--verbose', action='store_true',
            help='Give more info about what is going on.')
        self.parser.add_argument('--debug', action='store_true',
            help='Output bunches of debugging info.')

    def main(self):
        """ Main function.
        Entry point of the program.
        """
        try:
            from spec import Spec
            self.setup_parser()
            args = self.parser.parse_args()
            pypi = Pypi2spec(args.package)
            pypi.retrieve_info()
            pypi.download()
            pypi.extract_sources()
            pypi.determine_arch()
            pypi.remove_sources()
            settings = Settings()
            spec = Spec(settings, pypi)
            spec.fill_spec_info()
            spec.get_template()
            spec.write_spec()
        except Pypi2specError, err:
            print err

if __name__ == '__main__':
    Pypi2specUI().main()
