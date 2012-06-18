Name:           pypi2spec
Version:        0.2.0
Release:        1%{?dist}
Summary:        Python script to generate spec file for pypi projects

License:        GPLv3+
URL:            http://github.com/pypingou/pypi2spec
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python-devel,python-setuptools

Requires:       python-rdflib
Requires:       python-jinja2
Requires:       python-argparse

%description
pypi2spec makes your life easier by helping you to generate
spec file as close to the Fedora guidelines as possible for
project hosted on pypi.

%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT
install pypi2spec/specfile.tpl %{buildroot}/%{python_sitelib}/pypi2spec/
chmod -x %{buildroot}/%{python_sitelib}/pypi2spec/specfile.tpl

 
%files
%doc LICENSE README
%{python_sitelib}/*
%{_bindir}/%{name}

%changelog
* Mon Jun 18 2012 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.2.0-1
- Roll up a 0.2.0 release which includes a number of fixes from Ralph

* Mon Feb 27 2012 Ralph Bean <rbean@redhat.com> - 0.1.1-1
- Changed to use textwrap to format descriptions
- Changed to use setuptools instead of distutils
- Misc bugfixes

* Sat Feb 11 2012 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-1
- Initial package for Fedora
