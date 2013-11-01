%define name otrverwaltung
%define version 0.9.2
%define unmangled_version 0.9.2
%define release 1

Summary: Dateien von onlinetvrecorder.com verwalten
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: GPL-3
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Benjamin Elbers <elbersb@gmail.com>
Url: http://github.com/elbersb/otr-verwaltung

%description
Dateien von onlinetvrecorder.com verwalten: Schneiden, Schnitte betrachten, Cutlists bewerten...

%prep
%setup -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
