%global modname {{name}}

Name:             python-%{modname}
Version:          {{version}}
Release:          1%{?dist}
Summary:          {{summary}}

Group:            Development/Languages
License:          {{license}}
URL:              {{URL}}
Source0:          {{_source0}}

{% if (arch == False) %}BuildArch:        noarch
{% endif %}

BuildRequires:    python2-devel

%description
{{description}}

%prep
%setup -q -n %{modname}-%{version}

%build
{% if (arch == True) %} CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build
{% else %}%{__python} setup.py build {% endif %}

%install
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT


%files
%doc
{% if (arch == False) %}
%{python_sitelib}/%{modname}
%{python_sitelib}/%{modname}-%{version}*
{% else %}
%{python_sitearch}/%{modname}
%{python_sitearch}/%{modname}-%{version}*
{% endif %}

%changelog
* {{date}} {{packager}} <{{email}}> {{version}}-1
- initial package for Fedora
