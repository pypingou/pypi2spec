#-*- coding: utf-8 -*-

"""
 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc.,
 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

 (C) 2012 - Pierre-Yves Chibon <pingou@pingoured.fr>
"""
import ConfigParser
import argparse
import logging
import os
import shutil
import tarfile
import urllib2
from subprocess import Popen, PIPE
from tarfile import TarError


logging.basicConfig()
LOG = logging.getLogger('Pypi2spec')
#LOG.setLevel('DEBUG')
__version__ = '0.4.0'


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


def get_packager_name():
    """ Query rpm to retrieve a potential packager name from the
    .rpmmacros.
    """
    packager = get_rpm_tag('%packager')
    if not packager.startswith('%'):
        packager = packager.split('<')[0].strip()
        return packager
    else:
        return ''


def get_packager_email():
    """ Query rpm to retrieve a potential packager email from the
    .rpmmacros.
    """
    packager = get_rpm_tag('%packager')
    if not packager.startswith('%'):
        packager = packager.split('<', 1)[1].rsplit('>', 1)[0].strip()
        return packager
    else:
        return ''


class Settings(object):
    """ Pypi2spec user config Setting"""
    # Editor to use in the spec
    packager = get_packager_name()
    # Editor email to use in the spec
    email = get_packager_email()

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

    def __init__(self, message):
        """ Constructor. """
        super(Pypi2specError, self).__init__(message)
        self.message = message

    def __str__(self):
        """ Represent the error. """
        return str(self.message)


class Pypi2spec(object):
    """ Pypi2spec main class whose goal is to get the all the info
    needed for the spec file.
    """

    def __init__(self, name):
        """ Constructor.
        :arg name, the name of the library on the pypi website.
        """
        self.name = name
        self.description = ''
        self.log = get_logger()
        #self.log.setLevel(logging.DEBUG)
        self.version = ''
        self.summary = ''
        self.license = ''
        self.url = 'http://pypi.python.org/pypi/%s' % name
        self.source0 = ''
        self.source = ''
        self.tardir = ''
        self.arch = False

    def determine_arch(self):
        """ Determine if the package is arch or noarch by looking at the
        sources.
        Set arch to True if the package is arch dependant.
        Set arch to False if the package is noarch.
        Let arch to None if could not determine.
        """
        self.log.info('Determining if the package is arch dependant or not')
        extensions = ['c', 'C', 'cp', 'cpp', 'h', 'H', ]
        if os.path.exists(self.tardir):
            for root, dirs, files in os.walk(self.tardir):
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

    def __set_tardir(self, tfile):
        if isinstance(tarfile, basestring):
            tfile = tarfile.open(tfile)
        tar_names = tfile.getnames()
        self.tardir = tar_names[0]
        self.log.debug('self.tardir = %s', self.tardir)

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
            self.__set_tardir(sources)
            return

        url = self.source0.rsplit('/', 1)[0]
        url = '{url}/{source}'.format(url=url, source=self.source)
        self.log.info('Downloading %s' % url)

        try:
            remotefile = urllib2.urlopen(url)
        except urllib2.HTTPError, err:
            self.log.debug(err)
            raise Pypi2specError('Could not retrieve source: %s' % url)
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
            self.__set_tardir(tar)

            tar.close()
        except TarError, err:
            self.log.debug("Error while extracting the tarball")
            self.log.debug("ERROR: %s" % err)

    def remove_sources(self):
        """ Remove the source we extracted in the current working
        directory.
        """
        self.log.info('Removing extracted sources: "%s"' % self.tardir)
        try:
            shutil.rmtree(self.tardir)
        except (IOError, OSError), err:
            self.log.info('Could not remove the extracted sources: "%s"'
                          % self.tardir)
            self.log.debug('ERROR: %s' % err)

    def retrieve_info(self):
        """ Retrieve all the information from pypi to fill up the spec
        file.
        """
        import json
        import collections
        URLTEMPL = 'https://pypi.python.org/pypi/%s/json'
        try:
            fp = urllib2.urlopen(URLTEMPL % self.name)
            data = json.load(fp, object_pairs_hook=collections.OrderedDict)
        except urllib2.HTTPError as err:
            self.log.debug('ERROR while downloading metadata:\n  %s'
                           % err)
            raise Pypi2specError('Could not retrieve information for the'
                                 'project "%s". Did you make a typo?'
                                 % self.name)

        self.version = data[u'info'][u'version']
        self.summary = data[u'info'][u'summary']
        self.description = data[u'info'][u'description']

        self.source0 = [
            url['url']
            for url in data[u'urls']
            if url['url'].endswith('tar.gz') or url['url'].endswith('zip') or url['url'].endswith('whl')
        ][0]
        LOG.info('self.source0 = %s', self.source0)

        if not self.source0 \
            or os.path.splitext(self.source0)[1] not in \
                ['.gz', '.zip', '.bz2', '.whl']:
            LOG.debug("We don’t have good URL!")
            pypi_base = 'http://pypi.python.org/packages/source/'
            self.source0 = pypi_base + '%s/%s/%s-%s' % \
                (self.name[0], self.name, self.name, self.version)

            url_ext = False
            for ext in ['tar.gz', 'zip', 'tar.bz2']:
                url = '%s.%s' % (self.source0, ext)
                self.log.debug(url)
                try:
                    urllib2.urlopen(url)
                    url_ext = ext
                except urllib2.HTTPError, err:
                    self.log.debug(err)
            if url_ext is not False:
                self.source0 = '%s.%s' % (self.source0, url_ext)
                self.source = '%s-%s.%s' % (self.name, self.version,
                                            url_ext)
            else:
                raise Pypi2specError('No tarball or zip file could be '
                                     'found for this package: %s'
                                     % self.name)
        else:
            #self.source = '%s-%s.tar.gz' % (self.name, self.version)
            split_url = urllib2.urlparse.urlsplit(self.source0)
            self.source = os.path.basename(split_url.path)

        LOG.debug('self.source0 = %s', self.source0)
        LOG.debug('self.source = %s', self.source)


class Pypi2specUI(object):
    """ Class handling the user interface. """

    def __init__(self):
        """ Constructor.
        """
        self.parser = None
        self.log = get_logger()

    def setup_parser(self):
        """ Command line parser. """
        self.parser = argparse.ArgumentParser(usage='%(prog)s [options]',
                                              prog='pypi2spec')
        self.parser.add_argument('--version', action='version',
                                 version='%(prog)s ' + __version__)
        self.parser.add_argument('package',
                                 help='Name of the pypi library to package.')
        self.parser.add_argument('--python3', action='store_true',
                                 help='Create a specfile for both ' +
                                 'python2 and python3.')
        self.parser.add_argument('--verbose', action='store_true',
                                 help='Give more info about what is ' +
                                 'going on.')
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

            self.log = get_logger()
            if args.verbose:
                self.log.setLevel('INFO')
            if args.debug:
                self.log.setLevel('DEBUG')

            pypi = Pypi2spec(args.package)
            pypi.retrieve_info()
            pypi.download()
            pypi.extract_sources()
            pypi.determine_arch()
            pypi.remove_sources()
            settings = Settings()
            spec = Spec(settings, pypi, python3=args.python3)
            spec.fill_spec_info()
            spec.get_template()
            spec.write_spec()
        except Pypi2specError, err:
            print err


def main():
    """ Entry point used in the setup.py.
    This just calls the main function in Pypi2specUI.
    """
    return Pypi2specUI().main()

if __name__ == '__main__':
    #import sys
    #sys.argv.append('pypi2spec')
    main()
