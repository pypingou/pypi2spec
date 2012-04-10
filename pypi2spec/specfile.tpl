Name:             python-{{name}}
Version:          {{version}}
Release:          1%{?dist}
Summary:          {{summary}}

Group:            Development/Languages
License:          {{license}}
URL:              {{URL}}
Source0:          {{source0}}

{% if (arch == False) %}BuildArch:        noarch
{% endif %}

BuildRequires:    python2-devel

%description
{{description}}

%prep
%setup -q -n {{name}}-%{version}

%build
{% if (arch == True) %} CFLAGS="$RPM_OPT_FLAGS" %{__python} setup.py build
{% else %}%{__python} setup.py build {% endif %}

%install
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc
{% if (arch == False) %}
%{python_sitelib}/* {% else %}
%{python_sitearch}/*
{% endif %}

%changelog
* {{date}} {{packager}} <{{email}}> {{version}}-1
- initial package for Fedora
