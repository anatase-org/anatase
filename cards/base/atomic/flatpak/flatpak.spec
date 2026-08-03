%global appstream_version 1.0.0~
%global bubblewrap_version 0.10.0
%global glib_version 2.46.0
%global gpgme_version 1.8.0
%global libcurl_version 7.29.0
%global ostree_version 2020.8
%global wayland_protocols_version 1.32
%global wayland_scanner_version 1.15
%global xdg_portal_version 1.7.0

# Disable parental control for RHEL builds
%bcond malcontent %[!0%{?rhel}]

Name:           flatpak
Version:        1.18.0
Release:        %autorelease
Summary:        Application deployment framework for desktop apps

License:        LGPL-2.1-or-later
URL:            https://flatpak.org/
Source0:        https://github.com/flatpak/flatpak/releases/download/%{version}/%{name}-%{version}.tar.xz

Patch0:         overrides.patch

# ostree not on i686 for RHEL 10
# https://github.com/containers/composefs/pull/229#issuecomment-1838735764
%if 0%{?rhel} >= 10
ExcludeArch:    %{ix86}
%endif

BuildRequires:  pkgconfig(appstream) >= %{appstream_version}
BuildRequires:  pkgconfig(dconf)
BuildRequires:  pkgconfig(fuse3)
BuildRequires:  pkgconfig(gdk-pixbuf-2.0)
BuildRequires:  pkgconfig(gio-unix-2.0) >= %{glib_version}
BuildRequires:  pkgconfig(gobject-introspection-1.0) >= 1.40.0
BuildRequires:  pkgconfig(gpgme) >= %{gpgme_version}
BuildRequires:  pkgconfig(json-glib-1.0)
BuildRequires:  pkgconfig(libarchive) >= 2.8.0
BuildRequires:  pkgconfig(libseccomp)
BuildRequires:  pkgconfig(libcurl) >= %{libcurl_version}
BuildRequires:  pkgconfig(libsystemd)
BuildRequires:  pkgconfig(libxml-2.0) >= 2.4
BuildRequires:  pkgconfig(libzstd) >= 0.8.1
%if %{with malcontent}
BuildRequires:  pkgconfig(malcontent-0)
%endif
BuildRequires:  pkgconfig(ostree-1) >= %{ostree_version}
BuildRequires:  pkgconfig(polkit-gobject-1)
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-protocols) >= %{wayland_protocols_version}
BuildRequires:  pkgconfig(wayland-scanner) >= %{wayland_scanner_version}
BuildRequires:  pkgconfig(xau)
BuildRequires:  bison
BuildRequires:  bubblewrap >= %{bubblewrap_version}
BuildRequires:  docbook-dtds
BuildRequires:  docbook-style-xsl
BuildRequires:  gettext-devel
BuildRequires:  gtk-doc
BuildRequires:  libcap-devel
BuildRequires:  meson
BuildRequires:  python3-pyparsing
BuildRequires:  systemd
BuildRequires:  systemd-rpm-macros
BuildRequires:  /usr/bin/fusermount3
BuildRequires:  /usr/bin/pkcheck
BuildRequires:  /usr/bin/socat
BuildRequires:  /usr/bin/xdg-dbus-proxy
BuildRequires:  /usr/bin/xmlto
BuildRequires:  /usr/bin/xsltproc

Requires:       appstream%{?_isa} >= %{appstream_version}
Requires:       bubblewrap >= %{bubblewrap_version}
Requires:       glib2%{?_isa} >= %{glib_version}
Requires:       libcurl%{?_isa} >= %{libcurl_version}
Requires:       librsvg2%{?_isa}
Requires:       ostree-libs%{?_isa} >= %{ostree_version}
Requires:       /usr/bin/fusermount3
Requires:       /usr/bin/xdg-dbus-proxy
# https://fedoraproject.org/wiki/SELinux/IndependentPolicy
Requires:       (flatpak-selinux = %{?epoch:%{epoch}:}%{version}-%{release} if selinux-policy-targeted)
Requires:       %{name}-session-helper%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Recommends:     p11-kit-server
Recommends:     xdg-desktop-portal >= %{xdg_portal_version}

%description
flatpak is a system for building, distributing and running sandboxed desktop
applications on Linux. See https://wiki.gnome.org/Projects/SandboxedApps for
more information.

%package devel
Summary:        Development files for %{name}
Requires:       %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:       %{name}-libs%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}

%description devel
This package contains the pkg-config file and development headers for %{name}.

%package libs
Summary:        Libraries for %{name}
Requires:       bubblewrap >= %{bubblewrap_version}
# We can assume ostree is installed on ostree systems
# So do not enforce it on non-ostree ones
Requires:       ostree-libs%{?_isa} >= %{ostree_version}

%description libs
This package contains libflatpak.

%package selinux
Summary:        SELinux policy module for %{name}
BuildRequires:  selinux-policy
BuildRequires:  selinux-policy-devel
BuildRequires:  make
BuildArch:      noarch
%{?selinux_requires}

%description selinux
This package contains the SELinux policy module for %{name}.

%package session-helper
Summary:        User D-Bus service used by %{name} and others
Conflicts:      flatpak < 1.4.1-2
Requires:       systemd

%description session-helper
This package contains the org.freedesktop.Flatpak user D-Bus service
that's used by %{name} and other packages.

%package tests
Summary:        Tests for %{name}
Requires:       %{name}%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:       %{name}-libs%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:       %{name}-session-helper%{?_isa} = %{?epoch:%{epoch}:}%{version}-%{release}
Requires:       bubblewrap >= %{bubblewrap_version}
Requires:       ostree%{?_isa} >= %{ostree_version}

%description tests
This package contains installed tests for %{name}.


%prep
%autosetup -p1


%build
%meson \
    -Dinstalled_tests=true \
    -Dsystem_bubblewrap=/usr/bin/bwrap \
    -Dsystem_dbus_proxy=/usr/bin/xdg-dbus-proxy \
    -Dtmpfilesdir=%{_tmpfilesdir} \
%if %{with malcontent}
    -Dmalcontent=enabled \
%else
    -Dmalcontent=disabled \
%endif
    -Dwayland_security_context=enabled \
    %{nil}
%meson_build


%install
%meson_install
install -pm 644 NEWS README.md %{buildroot}/%{_pkgdocdir}
# The system repo is not installed by the flatpak build system.
install -d %{buildroot}%{_datadir}/%{name}/preinstall.d
install -d %{buildroot}%{_datadir}/%{name}/remotes.d
install -d %{buildroot}%{_localstatedir}/lib/flatpak
install -d %{buildroot}%{_sysconfdir}/%{name}/installations.d
install -d %{buildroot}%{_sysconfdir}/%{name}/preinstall.d
install -d %{buildroot}%{_sysconfdir}/flatpak/remotes.d

%find_lang %{name}


%post selinux
%selinux_modules_install %{_datadir}/selinux/packages/flatpak.pp.bz2


%postun selinux
if [ $1 -eq 0 ]; then
    %selinux_modules_uninstall %{_datadir}/selinux/packages/flatpak.pp.bz2
fi


%files -f %{name}.lang
%license COPYING
# Comply with the packaging guidelines about not mixing relative and absolute
# paths in doc.
%doc %{_pkgdocdir}
%{_bindir}/flatpak
%{_bindir}/flatpak-bisect
%{_bindir}/flatpak-coredumpctl
%{_datadir}/bash-completion
%{_datadir}/dbus-1/interfaces/org.freedesktop.portal.Flatpak.xml
%{_datadir}/dbus-1/interfaces/org.freedesktop.Flatpak.Authenticator.xml
%{_datadir}/dbus-1/services/org.flatpak.Authenticator.Oci.service
%{_datadir}/dbus-1/services/org.freedesktop.portal.Flatpak.service
%{_datadir}/dbus-1/system.d/org.freedesktop.Flatpak.SystemHelper.conf
%{_datadir}/dbus-1/system-services/org.freedesktop.Flatpak.SystemHelper.service
%{_datadir}/fish/
%{_datadir}/%{name}
%{_datadir}/polkit-1/actions/org.freedesktop.Flatpak.policy
%{_datadir}/polkit-1/rules.d/org.freedesktop.Flatpak.rules
%{_datadir}/zsh/site-functions
%{_libexecdir}/flatpak-oci-authenticator
%{_libexecdir}/flatpak-portal
%{_libexecdir}/flatpak-system-helper
%{_libexecdir}/flatpak-validate-icon
%{_libexecdir}/revokefs-fuse
%dir %{_localstatedir}/lib/flatpak
%{_mandir}/man1/%{name}*.1*
%{_mandir}/man5/%{name}-metadata.5*
%{_mandir}/man5/flatpak-flatpakref.5*
%{_mandir}/man5/flatpak-flatpakrepo.5*
%{_mandir}/man5/flatpak-installation.5*
%{_mandir}/man5/flatpak-remote.5*
%{_mandir}/man5/flatpakref.5*
%{_mandir}/man5/flatpakrepo.5*
%dir %{_sysconfdir}/flatpak
%{_sysconfdir}/%{name}/installations.d
%{_sysconfdir}/%{name}/preinstall.d
%{_sysconfdir}/flatpak/remotes.d
%{_sysconfdir}/profile.d/flatpak.csh
%{_sysconfdir}/profile.d/flatpak.sh
%{_sysusersdir}/%{name}.conf
%{_unitdir}/flatpak-system-helper.service
%{_userunitdir}/flatpak-oci-authenticator.service
%{_userunitdir}/flatpak-portal.service
%{_systemd_system_env_generator_dir}/60-flatpak-system-only
%{_systemd_user_env_generator_dir}/60-flatpak
%{_tmpfilesdir}/%{name}.conf

%files devel
%{_datadir}/gir-1.0/Flatpak-1.0.gir
%{_datadir}/gtk-doc/
%{_includedir}/%{name}/
%{_libdir}/libflatpak.so
%{_libdir}/pkgconfig/%{name}.pc

%files libs
%license COPYING
%{_libdir}/girepository-1.0/Flatpak-1.0.typelib
%{_libdir}/libflatpak.so.*

%files selinux
%{_datadir}/selinux/packages/flatpak.pp.bz2
%{_datadir}/selinux/devel/include/distributed/flatpak.if

%files session-helper
%license COPYING
%{_datadir}/dbus-1/interfaces/org.freedesktop.Flatpak.xml
%{_datadir}/dbus-1/services/org.freedesktop.Flatpak.service
%{_libexecdir}/flatpak-session-helper
%{_userunitdir}/flatpak-session-helper.service

%files tests
%{_datadir}/installed-tests
%{_libexecdir}/installed-tests


%changelog
%autochangelog
