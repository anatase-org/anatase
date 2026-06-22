Name:		anatase-logos
Summary:	Anatase-related icons and pictures
Version:	42.0.1
Release:	4%{?dist}

License:	LicenseRef-Anatase-Logos
Source0:	favicon.svg
Source1:	letterhead-onblack.svg
Source2:	letterhead-onwhite.svg
Source3:	COPYING
Provides:	redhat-logos = %{version}-%{release}
Provides:	gnome-logos = %{version}-%{release}
Provides:	system-logos = %{version}-%{release}
BuildArch:	noarch
BuildRequires:	hardlink
BuildRequires:	librsvg2-tools

%description
The anatase-logos package contains image files which incorporate the
Anatase trademarks (the "Marks"). This package and its content may not be
distributed with anything but unmodified Anatase images and images for
personal and internal organisation use.

%prep
cp -p %{SOURCE3} COPYING

%build
builddir=%{_builddir}/%{name}-generated
rm -rf "$builddir"
mkdir -p "$builddir"/icons/hicolor/scalable/apps
mkdir -p "$builddir"/pixmaps
mkdir -p "$builddir"/plymouth/themes/spinner

cp -p %{SOURCE0} "$builddir"/icons/hicolor/scalable/apps/anatase-logo-icon.svg

rsvg-convert -a -w 252 -h 252 -o "$builddir"/pixmaps/anatase-logo-sprite.png %{SOURCE0}
rsvg-convert -a -w 252 -h 252 -o "$builddir"/pixmaps/system-logo-white.png %{SOURCE1}
rsvg-convert -a -w 149 -h 43 -o "$builddir"/plymouth/themes/spinner/watermark.png %{SOURCE1}

for size in 16 22 24 32 36 48 96 256 ; do
  mkdir -p "$builddir"/icons/hicolor/${size}x${size}/apps
  rsvg-convert -a -w "$size" -h "$size" -o "$builddir"/icons/hicolor/${size}x${size}/apps/anatase-logo-icon.png %{SOURCE0}
done

%install
# Cockpit and KDE About System use these pixmaps.
mkdir -p $RPM_BUILD_ROOT%{_datadir}/pixmaps
install -p -m 644 %{_builddir}/%{name}-generated/pixmaps/anatase-logo-sprite.png $RPM_BUILD_ROOT%{_datadir}/pixmaps/
install -p -m 644 %{_builddir}/%{name}-generated/pixmaps/system-logo-white.png $RPM_BUILD_ROOT%{_datadir}/pixmaps/
pushd $RPM_BUILD_ROOT%{_datadir}/pixmaps
  ln -s anatase-logo-sprite.png fedora-logo-sprite.png
popd

# The Plymouth spinner theme logo bit.
mkdir -p $RPM_BUILD_ROOT%{_datadir}/plymouth/themes/spinner
install -p -m 644 %{_builddir}/%{name}-generated/plymouth/themes/spinner/watermark.png $RPM_BUILD_ROOT%{_datadir}/plymouth/themes/spinner/watermark.png

# Logo icons used by os-release LOGO and as the Plasma launcher icon.
for size in 16x16 22x22 24x24 32x32 36x36 48x48 96x96 256x256 ; do
  mkdir -p $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/$size/apps
  install -p -m 644 %{_builddir}/%{name}-generated/icons/hicolor/$size/apps/anatase-logo-icon.png $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/$size/apps/
  pushd $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/$size/apps
    ln -s anatase-logo-icon.png fedora-logo-icon.png
  popd
done

for i in 16 22 24 32 36 48 96 256 ; do
  mkdir -p $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/${i}x${i}/places
  pushd $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/${i}x${i}/places
    ln -s ../apps/anatase-logo-icon.png start-here.png
  popd
done

# Favicon path used by Cockpit's Fedora branding symlink.
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}
pushd $RPM_BUILD_ROOT%{_sysconfdir}
  ln -s %{_datadir}/icons/hicolor/16x16/apps/fedora-logo-icon.png favicon.png
popd

# Hicolor scalable launcher icon.
mkdir -p $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/scalable/apps
install -p -m 644 %{_builddir}/%{name}-generated/icons/hicolor/scalable/apps/anatase-logo-icon.svg $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/scalable/apps/
pushd $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/scalable/apps
  ln -s anatase-logo-icon.svg fedora-logo-icon.svg
  ln -s anatase-logo-icon.svg start-here.svg
popd
mkdir -p $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/scalable/places/
pushd $RPM_BUILD_ROOT%{_datadir}/icons/hicolor/scalable/places/
  ln -s ../apps/start-here.svg .
popd

# save some dup'd icons
# Except in /boot. Because some people think it is fun to use VFAT for /boot.
# hardlink is /usr/sbin/hardlink on Fedora <= 30 and /usr/bin/hardlink on F31+
hardlink -vv %{buildroot}/usr

%files
%license COPYING
%config(noreplace) %{_sysconfdir}/favicon.png
%{_datadir}/plymouth/themes/spinner/
%{_datadir}/pixmaps/anatase-logo-sprite.png
%{_datadir}/pixmaps/fedora-logo-sprite.png
%{_datadir}/pixmaps/system-logo-white.png
%{_datadir}/icons/hicolor/*/apps/anatase-logo-icon.png
%{_datadir}/icons/hicolor/*/apps/fedora-logo-icon.png
%{_datadir}/icons/hicolor/*/places/start-here.png
%{_datadir}/icons/hicolor/scalable/apps/anatase-logo-icon.svg
%{_datadir}/icons/hicolor/scalable/apps/fedora-logo-icon.svg
%{_datadir}/icons/hicolor/scalable/apps/start-here.svg
%{_datadir}/icons/hicolor/scalable/places/start-here.svg
# we multi-own these directories, so as not to require the packages that
# provide them, thereby dragging in excess dependencies.
%dir %{_datadir}/icons/hicolor/
%dir %{_datadir}/icons/hicolor/16x16/
%dir %{_datadir}/icons/hicolor/16x16/apps/
%dir %{_datadir}/icons/hicolor/16x16/places/
%dir %{_datadir}/icons/hicolor/22x22/
%dir %{_datadir}/icons/hicolor/22x22/apps/
%dir %{_datadir}/icons/hicolor/22x22/places/
%dir %{_datadir}/icons/hicolor/24x24/
%dir %{_datadir}/icons/hicolor/24x24/apps/
%dir %{_datadir}/icons/hicolor/24x24/places/
%dir %{_datadir}/icons/hicolor/32x32/
%dir %{_datadir}/icons/hicolor/32x32/apps/
%dir %{_datadir}/icons/hicolor/32x32/places/
%dir %{_datadir}/icons/hicolor/36x36/
%dir %{_datadir}/icons/hicolor/36x36/apps/
%dir %{_datadir}/icons/hicolor/36x36/places/
%dir %{_datadir}/icons/hicolor/48x48/
%dir %{_datadir}/icons/hicolor/48x48/apps/
%dir %{_datadir}/icons/hicolor/48x48/places/
%dir %{_datadir}/icons/hicolor/96x96/
%dir %{_datadir}/icons/hicolor/96x96/apps/
%dir %{_datadir}/icons/hicolor/96x96/places/
%dir %{_datadir}/icons/hicolor/256x256/
%dir %{_datadir}/icons/hicolor/256x256/apps/
%dir %{_datadir}/icons/hicolor/256x256/places/
%dir %{_datadir}/icons/hicolor/scalable/
%dir %{_datadir}/icons/hicolor/scalable/apps/
%dir %{_datadir}/icons/hicolor/scalable/places/
%dir %{_datadir}/plymouth/

%package -n fedora-logos
Summary:	Empty compatibility package for Fedora logo dependencies
Requires:	%{name} = %{version}-%{release}
BuildArch:	noarch

%description -n fedora-logos
This empty package exists to satisfy dependencies that require the Fedora
logo package by name. The actual logo files are provided by anatase-logos.

%files -n fedora-logos

%changelog
