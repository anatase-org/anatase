%bcond_without check

# vpower only ships a binary.
%global cargo_install_lib 0
%global debug_package %{nil}

Name:           vpower
Version:        1.6.2
Release:        %autorelease
Summary:        Daemon for calculating Steam battery metrics

License:        MIT
URL:            https://github.com/evlaV/vpower
Source0:        %{url}/archive/%{version}/%{name}-%{version}.tar.gz
Source1:        vpower.tmpfiles
Patch0:         overrides.patch

BuildRequires:  cargo
BuildRequires:  cargo-rpm-macros >= 26
BuildRequires:  rust
BuildRequires:  rust-packaging
BuildRequires:  rust-std-static
BuildRequires:  systemd-rpm-macros
BuildRequires:  lm_sensors-devel
BuildRequires:  (crate(lazy_static/default) >= 1.5.0 with crate(lazy_static/default) < 2.0.0~)
BuildRequires:  (crate(libc/default) >= 0.2.0 with crate(libc/default) < 0.3.0~)

%description
vpower calculates battery charge, status, and remaining-time metrics for Steam.

%prep
# Keep an empty, newly initialized overrides.patch valid until it gains its
# first patchwork commit.
%autosetup -N -n %{name}-%{version}
if test -s %{PATCH0}; then
    %autopatch -p1
fi

%cargo_prep

%build
%cargo_build
%{cargo_license_summary}
%{cargo_license} > LICENSE.dependencies

%install
install -Dpm0755 target/rpm/vpower %{buildroot}%{_prefix}/lib/vpower
install -Dpm0644 %{SOURCE1} %{buildroot}%{_tmpfilesdir}/vpower.conf

%check
%cargo_test

%files
%license LICENSE LICENSE.dependencies
%{_prefix}/lib/vpower
%{_tmpfilesdir}/vpower.conf

%changelog
%autochangelog
