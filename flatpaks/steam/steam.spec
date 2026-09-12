%global debug_package %{nil}
%global appstream_id com.valvesoftware.Steam
%global arm_client_source_id dc817d33f8308815bf4fde6a3cb61fd4529728c8

Name:           steam
Version:        1.0.0.86
Release:        1%{?dist}
Summary:        Installer for the Steam software distribution service
# Redistribution and repackaging for Linux is allowed, see license file
License:        Steam License Agreement
URL:            http://www.steampowered.com/
ExclusiveArch:  x86_64 aarch64

Source0:        https://repo.steampowered.com/%{name}/archive/beta/%{name}_%{version}.tar.gz
%ifarch aarch64
Source1:        https://client-update.steamstatic.com/bins_linuxarm64_linuxarm64.zip.%{arm_client_source_id}
%endif

# Do not install desktop file in lib/steam, do not install apt sources
Patch0:         %{name}-makefile.patch
# Do not try to copy steam.desktop to the user's desktop from lib/steam
Patch1:         %{name}-no-icon-on-desktop.patch
%ifarch aarch64
# Select and launch the native ARM bootstrap through the standard installer path
Patch2:         %{name}-arm64-bootstrap.patch
%endif

BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib
BuildRequires:  make
BuildRequires:  systemd
%ifarch aarch64
BuildRequires:  tar
BuildRequires:  unzip
BuildRequires:  xz
%endif

%ifarch x86_64
# Required for the basic runtime
Requires:       glibc(x86-32)
Requires:       libdrm(x86-32)
Requires:       libglvnd-glx(x86-32)
Requires:       libnsl(x86-32)

# Required to run the initial setup
Requires:       tar
Requires:       zenity
Requires:       xz

# Required for basic gaming, also for native 32 bit games:
Requires:       mesa-dri-drivers
Requires:       mesa-dri-drivers(x86-32)
Requires:       mesa-vulkan-drivers
Requires:       mesa-vulkan-drivers(x86-32)
Requires:       vulkan-loader
Requires:       vulkan-loader(x86-32)
%endif

# Hardware stuff (permissions on devices, hardware updater, etc.):
Requires:       steam-devices

# Required by Feral interactive games
Requires:       libatomic
%ifarch x86_64
Requires:       libatomic(x86-32)
%endif

# Proton uses xdg-desktop-portal to open URLs from inside a container
Requires:       xdg-desktop-portal
Recommends:     (xdg-desktop-portal-gtk if gnome-shell)
Recommends:     (xdg-desktop-portal-kde if kwin)

# Prevent log spam when thse are not pulled in as dependencies of full desktops
Recommends:     dbus-x11
Recommends:     xdg-user-dirs

# Allow using Steam Runtime Launch Options
Recommends:     gobject-introspection

# Automatic loading of the ntsync module
Recommends:     ntsync-autoload

%description
Steam is a software distribution service with an online store, automated
installation, automatic updates, achievements, SteamCloud synchronized savegame
and screenshot functionality, and many social features.

This package contains the installer for the Steam software distribution service.

%ifarch x86_64
%package arch-transition
Summary: Transition package for migrating Steam from i686 to x86_64
Requires: %{name} = %{version}-%{release}
Provides: steam = 1.0.0.85-8
Obsoletes: steam < 1.0.0.85-8
BuildArch: noarch

%description arch-transition
This package is used to migrate Steam installations from the
legacy i686 package layout to the x86_64 package layout.

It exists only to handle package replacement and dependency
changes during upgrades, and can be safely removed once the
transition is complete.
%endif

%prep
%autosetup -p1 -n %{name}-launcher

%build
# Nothing to build

%install
%make_install PREFIX=%{_prefix}

rm -fr \
    %{buildroot}%{_docdir}/%{name}/ \
    %{buildroot}%{_bindir}/%{name}deps

%ifarch aarch64
rm -f %{buildroot}%{_prefix}/lib/%{name}/bootstraplinux_ubuntu12_32.tar.xz

arm_bootstrap=arm-bootstrap
rm -rf "${arm_bootstrap}"
mkdir -p "${arm_bootstrap}"
unzip -q %{SOURCE1} -d "${arm_bootstrap}"

# The archive does not carry executable mode bits for its native binaries.
chmod 0755 \
    "${arm_bootstrap}"/steamrtarm64/fossilize_replay \
    "${arm_bootstrap}"/steamrtarm64/gameoverlayui \
    "${arm_bootstrap}"/steamrtarm64/gldriverquery \
    "${arm_bootstrap}"/steamrtarm64/reaper \
    "${arm_bootstrap}"/steamrtarm64/steam \
    "${arm_bootstrap}"/steamrtarm64/steam_monitor \
    "${arm_bootstrap}"/steamrtarm64/steamerrorreporter \
    "${arm_bootstrap}"/steamrtarm64/steamsysinfo \
    "${arm_bootstrap}"/steamrtarm64/steamwebhelper \
    "${arm_bootstrap}"/steamrtarm64/steamwebhelper.sh \
    "${arm_bootstrap}"/steamrtarm64/streaming_client \
    "${arm_bootstrap}"/steamrtarm64/vgui_panel_zoo \
    "${arm_bootstrap}"/steamrtarm64/vulkandriverquery

# Restore links whose ZIP entries use DOS path separators.
ln -sfn libcurl.so.4.8.0 "${arm_bootstrap}"/steamrtarm64/libs/libcurl.so
ln -sfn libnghttp2.so.14.20.1 "${arm_bootstrap}"/steamrtarm64/libs/libnghttp2.so
ln -sfn libnghttp2.so.14.20.1 "${arm_bootstrap}"/steamrtarm64/libs/libnghttp2.so.14

tar -C "${arm_bootstrap}" -cJf \
    %{buildroot}%{_prefix}/lib/%{name}/bootstraplinux_linuxarm64.tar.xz .
%endif

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/%{appstream_id}.metainfo.xml

%files
%license COPYING steam_subscriber_agreement.txt
%doc debian/changelog
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/*/apps/%{name}.png
%{_datadir}/pixmaps/%{name}.png
%{_datadir}/pixmaps/%{name}_tray_mono.png
%{_prefix}/lib/%{name}/
%{_mandir}/man6/%{name}.*
%{_metainfodir}/%{appstream_id}.metainfo.xml

%ifarch x86_64
%files arch-transition
%endif

%changelog
