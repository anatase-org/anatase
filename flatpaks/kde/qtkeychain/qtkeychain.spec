%bcond_without qt5
%bcond_without qt6

Name:           qtkeychain
Version:        0.16.0
Release:        %autorelease
Summary:        A password store library

License:        BSD-3-Clause
Url:            https://github.com/frankosterfeld/qtkeychain
Source0:        %{url}/archive/%{version}/%{name}-%{version}.tar.gz

BuildRequires:  make
BuildRequires:  gcc-c++
BuildRequires:  cmake
BuildRequires:  pkgconfig(libsecret-1)

%description
The qtkeychain library allows you to store passwords easily and securely.


%if %{with qt5}
%package qt5
Summary:        %{summary}

%description qt5
The qt5keychain library allows you to store passwords easily and securely.


%package qt5-devel
Summary:        Development files for %{name}-qt5
BuildRequires:  cmake(Qt5Core)
BuildRequires:  cmake(Qt5LinguistTools)
Requires:       %{name}-qt5%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:       qt5-qtbase-devel%{?_isa}
# deps referenced in Qt5KeychainLibraryDepends-relwithdebinfo.cmake:  IMPORTED_LINK_INTERFACE_LIBRARIES_RELWITHDEBINFO "Qt5::Core;secret-1;gio-2.0;gobject-2.0;glib-2.0;Qt5::DBus"
# *probably* overlinking and can be pruned, but requires closer inspection
Requires:       pkgconfig(libsecret-1)

%description qt5-devel
This package contains development files for qt5keychain.
%endif


%if %{with qt6}
%package qt6
Summary:        %{summary}

%description qt6
The qt6keychain library allows you to store passwords easily and securely.


%package qt6-devel
Summary:        Development files for %{name}-qt6
BuildRequires:  cmake(Qt6Core)
BuildRequires:  cmake(Qt6LinguistTools)
Requires:       %{name}-qt6%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:       qt6-qtbase-devel%{?_isa}
# deps referenced in Qt6KeychainLibraryDepends-relwithdebinfo.cmake:  IMPORTED_LINK_INTERFACE_LIBRARIES_RELWITHDEBINFO "Qt6::Core;secret-1;gio-2.0;gobject-2.0;glib-2.0;Qt6::DBus"
# *probably* overlinking and can be pruned, but requires closer inspection
Requires:       pkgconfig(libsecret-1)

%description qt6-devel
This package contains development files for qt6keychain.
%endif


%prep
%autosetup -p1


%build
%if %{with qt5}
%define _vpath_builddir %{_target_platform}-qt5
%cmake \
  -DBUILD_WITH_QT6:BOOL=OFF \
  -DECM_MKSPECS_INSTALL_DIR=%{_qt5_archdatadir}/mkspecs/modules \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo
%cmake_build
%endif

%if %{with qt6}
%define _vpath_builddir %{_target_platform}-qt6
%cmake \
  -DBUILD_WITH_QT6:BOOL=ON \
  -DECM_MKSPECS_INSTALL_DIR=%{_qt6_archdatadir}/mkspecs/modules \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo
%cmake_build
%endif


%install
%if %{with qt5}
%define _vpath_builddir %{_target_platform}-qt5
%cmake_install
%endif

%if %{with qt6}
%define _vpath_builddir %{_target_platform}-qt6
%cmake_install
%endif

%find_lang %{name} --with-qt
grep %{_datadir}/qt5keychain/translations %{name}.lang > %{name}-qt5.lang
grep %{_datadir}/qt6keychain/translations %{name}.lang > %{name}-qt6.lang


%if %{with qt5}
%files qt5 -f %{name}-qt5.lang
%license COPYING
%{_libdir}/libqt5keychain.so.1
%{_libdir}/libqt5keychain.so.0*

%files qt5-devel
%{_includedir}/qt5keychain/
%{_libdir}/cmake/Qt5Keychain/
%{_libdir}/libqt5keychain.so
%{_qt5_archdatadir}/mkspecs/modules/qt_Qt5Keychain.pri
%endif

%if %{with qt6}
%files qt6 -f %{name}-qt6.lang
%license COPYING
%{_libdir}/libqt6keychain.so.1
%{_libdir}/libqt6keychain.so.0*

%files qt6-devel
%{_includedir}/qt6keychain/
%{_libdir}/cmake/Qt6Keychain/
%{_libdir}/libqt6keychain.so
%{_qt6_archdatadir}/mkspecs/modules/qt_Qt6Keychain.pri
%endif

%changelog
%autochangelog
