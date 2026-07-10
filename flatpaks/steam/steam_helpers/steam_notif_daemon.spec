Name:           steam_notif_daemon
Version:        1.0.1
Release:        %autorelease
Summary:        Notification daemon forwarding desktop notifications to Steam

License:        MIT
URL:            https://github.com/evlav/steam_notif_daemon
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  gcc
BuildRequires:  meson
BuildRequires:  pkgconfig(libcurl)
BuildRequires:  pkgconfig(libsystemd)

%description
%{name} implements org.freedesktop.Notifications and forwards notifications to
the running Steam client.

%prep
%autosetup -n %{name}-%{version}

%build
%meson -Dsd-bus-provider=libsystemd
%meson_build

%install
%meson_install

%files
%license LICENSE
%doc README.md
%{_bindir}/steam_notif_daemon

%changelog
%autochangelog
