{% if python3 == True %}%if 0%{?fedora} > 12 || 0%{?rhel} > 6
%global with_python3 1
%endif{%endif%}

%global modname {{name}}

Name:             %{modname}
Version:          {{version}}
Release:          1%{?dist}
Summary:          {{summary}}

Group:            Development/Libraries
License:          {{license}}
URL:              {{URL}}
Source0:          {{_source0}}

{% if (arch == False) %}BuildArch:        noarch
{% endif %}

BuildRequires:    python2-devel

{%if python3%}%if 0%{?with_python3}
BuildRequires:    python3-devel
%endif{%endif%}

%description
{{description}}

{%if python3%}%if 0%{?with_python3}
%package -n python3-{{name}}
Summary:        {{summary}}
Group:          Development/Libraries

%description -n python3-{{name}}
{{description}}
%endif{%endif%}

%prep
%setup -q -n %{modname}-%{version}

# Remove bundled egg-info in case it exists
rm -rf %{modname}.egg-info
{%if python3%}%if 0%{?with_python3}
rm -rf %{py3dir}
cp -a . %{py3dir}
%endif{%endif%}

%build
{% if (arch == True) %}CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build
{%if python3%}%if 0%{?with_python3}
pushd %{py3dir}
CFLAGS="$RPM_OPT_FLAGS" %{__python3} setup.py build
popd
%endif{%endif%}{% else %}%{__python} setup.py build
{%if python3%}%if 0%{?with_python3}
pushd %{py3dir}
%{__python3} setup.py build
popd
%endif
{% endif %}{%endif%}

%install
{%if python3%}%if 0%{?with_python3}
pushd %{py3dir}
%{__python3} setup.py install -O1 --skip-build --root=%{buildroot}
popd
%endif{%endif%}
%{__python} setup.py install -O1 --skip-build --root=%{buildroot}

%check
%{__python} setup.py test
{%if python3%}%if 0%{?with_python3}
pushd %{py3dir}
%{__python3} setup.py test
popd
%endif{%endif%}

%files
%doc README.rst LICENSE
{% if (arch == False) %}%{python_sitelib}/%{modname}
%{python_sitelib}/%{modname}-%{version}*
{% else %}%{python_sitearch}/%{modname}
%{python_sitearch}/%{modname}-%{version}*
{% endif %}
{%if python3%}%if 0%{?with_python3}
%files -n python3-%{modname}
%doc LICENSE README.rst
{% if (arch == False) %}%{python3_sitelib}/%{modname}
%{python3_sitelib}/%{modname}-%{version}-*
{% else %}%{python3_sitearch}/%{modname}
%{python3_sitearch}/%{modname}-%{version}*
{% endif %}
%endif{%endif%}

%changelog
* {{date}} {{packager}} <{{email}}> {{version}}-1
- initial package for Fedora
