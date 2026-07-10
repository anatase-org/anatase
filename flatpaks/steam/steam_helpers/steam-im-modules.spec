%global source_tag jupiter-20240131

Name:           steam-im-modules
Version:        20240131
Release:        %autorelease
Summary:        Steam virtual keyboard input method modules

License:        LGPL-2.1-only AND LGPL-2.1-or-later
URL:            https://github.com/valve-project/steam-qt-keyboard-plugin
Source0:        %{url}/archive/%{source_tag}/steam-qt-keyboard-plugin-%{source_tag}.tar.gz

BuildRequires:  cmake
BuildRequires:  extra-cmake-modules
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  gtk3-devel
BuildRequires:  gtk4-devel
BuildRequires:  qt5-qtbase-devel
BuildRequires:  qt5-qtbase-private-devel

%description
%{name} provides Qt5, GTK3, and GTK4 input method modules that request the
Steam virtual keyboard.

%prep
%autosetup -n steam-qt-keyboard-plugin-%{source_tag}

%build
%cmake \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  -DKDE_INSTALL_QTPLUGINDIR=%{_libdir}/qt5/plugins
%cmake_build

%install
%cmake_install

%files
%doc README.md
%{_libdir}/qt5/plugins/platforminputcontexts/steam-qt-keyboard-plugin.so
%{_libdir}/gtk-3.0/3.0.0/immodules/im-steam.so
%{_libdir}/gtk-4.0/4.0.0/immodules/libim-steam.so

%changelog
%autochangelog
