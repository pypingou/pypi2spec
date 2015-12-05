%if 0%{?fedora}
%global with_python3 1
%endif

%{!?_licensedir: %global license %%doc}

%if 0%{?rhel} && 0%{?rhel} <= 6
%{!?__python2:        %global __python2 /usr/bin/python2}
%{!?python2_sitelib:  %global python2_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python2_sitearch: %global python2_sitearch %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%global modname {{modname}}
%global sum     {{summary}}

Name:               python-{{barename}}
Version:            {{version}}
Release:            1%{?dist}
Summary:            %{sum}

License:            {{license}}
URL:                {{URL}}
Source0:            {{_source0}}

{% if (arch == False) -%}
BuildArch:          noarch
{%- endif %}

BuildRequires:      python2-devel
BuildRequires:      python2-setuptools
%if 0%{?with_python3}
BuildRequires:      python3-devel
BuildRequires:      python3-setuptools
%endif

%description
{{description}}

%package -n python2-%{modname}
Summary:            {{summary}}
%{?python_provide:%python_provide python2-%{module}}

Requires:           python2-...

%description -n python2-%{modname}
{{description}}


%if 0%{?with_python3}
%package -n python3-%{modname}
Summary:            {{summary}}
%{?python_provide:%python_provide python3-%{module}}

Requires:           python3-...

%description -n python3-%{modname}
{{description}}
%endif

%prep
%autosetup -n %{modname}-%{version}

%build
%py2_build
%if 0%{?with_python3}
%py3_build
%endif

%install
%py2_install
%if 0%{?with_python3}
%py3_install
%endif

%check
%{__python2} setup.py test
%if 0%{?with_python3}
%{__python3} setup.py test
%endif

%files -n python2-%{modname}
%doc README.rst
%license LICENSE
{% if (arch == False) -%}
%{python2_sitelib}/%{modname}/
%{python2_sitelib}/%{modname}-%{version}*
{%- else -%}
%{python2_sitearch}/%{modname}/
%{python2_sitearch}/%{modname}-%{version}*
{%- endif %}

%if 0%{?with_python3}
%files -n python3-%{modname}
%doc README.rst
%license LICENSE
{% if (arch == False) -%}
%{python3_sitelib}/%{modname}/
%{python3_sitelib}/%{modname}-%{version}-*
{%- else -%}
%{python3_sitearch}/%{modname}/
%{python3_sitearch}/%{modname}-%{version}*
{%- endif -%}
%endif

%changelog
* {{date}} {{packager}} <{{email}}> {{version}}-1
- Initial packaging for Fedora.
