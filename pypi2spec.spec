Name:           pypi2spec
Version:        0.5.0
Release:        1%{?dist}
Summary:        Python script to generate RPM spec file for PyPI projects
License:        GPLv3+
URL:            http://github.com/pypingou/pypi2spec
Source0:        http://pypi.python.org/packages/source/p/%{name}/%{name}-%{version}.tar.gz
BuildArch:      noarch
BuildRequires:  python2-devel,python-setuptools
Requires:       python-jinja2
Requires:       python-argparse

%description
pypi2spec makes your life easier by helping you to generate RPM
spec file as close to the Fedora guidelines as possible for
project hosted on PyPI.

%prep
%setup -q

%build
%{__python2} setup.py build

%install
%{__python2} setup.py install -O1 --skip-build --root %{buildroot}
install -pm644 pypi2spec/specfile.tpl %{buildroot}%{python2_sitelib}/pypi2spec/

%files
%doc LICENSE README
%{_bindir}/%{name}
%{python2_sitelib}/*

%changelog
* Fri Feb 05 2016 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.5.0-1
- Update spec template to the latest guidelines

* Tue Sep 30 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.0-2
- Drop python-rdflib as a Requires

* Tue Sep 30 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.0-1
- Update to 0.4.0
- Drop the doap format in favor of the json output

* Tue Dec 10 2013 Christopher Meng <rpm@cicku.me> - 0.3.0-2
- Beautify SPEC syntax.

* Mon Dec 17 2012 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.3.0-1
- Update to 0.3.0

* Mon Jun 18 2012 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.2.2-1
- Roll up a 0.2.2 release with the correct download url in the setup.py
- Fix the Source0 url

* Mon Jun 18 2012 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.2.0-1
- Roll up a 0.2.0 release which includes a number of fixes from Ralph

* Mon Feb 27 2012 Ralph Bean <rbean@redhat.com> - 0.1.1-1
- Changed to use textwrap to format descriptions
- Changed to use setuptools instead of distutils
- Misc bugfixes

* Sat Feb 11 2012 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-1
- Initial package for Fedora
