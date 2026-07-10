%global commit 5ad92bfab460cd8ea536831789c43590b3a7a71c
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Name:           xdg-desktop-portal-holo
Version:        0.1.18.%{shortcommit}
Release:        %autorelease
Summary:        Steam backend for xdg-desktop-portal when running in Gamescope

License:        BSD-3-Clause AND LGPL-2.1-or-later
URL:            https://github.com/evlav/xdg-desktop-portal-holo
Source0:        %{url}/archive/%{commit}/%{name}-%{shortcommit}.tar.gz
Source1:        steam-http-loader
Source2:        steam_http_loader.desktop
Source3:        gamescope-mimeapps.list

BuildRequires:  desktop-file-utils
BuildRequires:  gcc
BuildRequires:  meson
BuildRequires:  pkgconfig(fontconfig)
BuildRequires:  pkgconfig(gio-2.0)
BuildRequires:  pkgconfig(gio-unix-2.0)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(systemd)
BuildRequires:  pkgconfig(xdg-desktop-portal)

Requires:       flatpak
Requires:       python3
Provides:       xdg-desktop-portal-impl

%description
%{name} provides the AppChooser, Email, Lockdown, and Settings portal
interfaces used by Steam in Gamescope session.

%prep
%autosetup -n %{name}-%{commit}
sed -i 's/SteamOS/steam/g' \
  data/meson.build \
  src/lockdown.c \
  src/settings.c

%build
%meson -Dwerror=false
%meson_build

%install
%meson_install

install -Dpm0755 %{SOURCE1} %{buildroot}%{_bindir}/steam-http-loader
install -Dpm0644 %{SOURCE2} %{buildroot}%{_datadir}/applications/steam_http_loader.desktop
install -Dpm0644 %{SOURCE3} %{buildroot}%{_datadir}/applications/gamescope-mimeapps.list

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/steam_http_loader.desktop

%files
%license LICENSES/BSD-3-Clause.txt LICENSES/LGPL-2.1-or-later.txt
%doc README.md
%{_bindir}/steam-http-loader
%{_libexecdir}/xdg-desktop-portal-holo
%{_datadir}/applications/gamescope-mimeapps.list
%{_datadir}/applications/steam_http_loader.desktop
%{_datadir}/applications/xdg-desktop-portal-holo.desktop
%{_datadir}/dbus-1/services/org.freedesktop.impl.portal.desktop.holo.service
%{_datadir}/xdg-desktop-portal/gamescope-portals/holo.portal
%{_sysconfdir}/xdg/steam/portal/lockdown.conf
%{_sysconfdir}/xdg/steam/portal/settings.conf
%{_userunitdir}/xdg-desktop-portal-holo.service

%changelog
%autochangelog
