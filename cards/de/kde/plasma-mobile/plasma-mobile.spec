# https://fedoraproject.org/wiki/Changes/EncourageI686LeafRemoval
ExcludeArch: %{ix86}

Name:           plasma-mobile
Version:        6.7.4
Release:        1%{?dist}
License:        CC0-1.0 AND GPL-2.0-only AND GPL-2.0-or-later AND GPL-3.0-only AND GPL-3.0-or-later AND LGPL-2.0-or-later AND LGPL-2.0-only AND LGPL-2.0-or-later AND LGPL-2.1-or-later AND LGPL-3.0-only AND LGPL-3.0-only AND MIT
Summary:        General UI components for Plasma Phone including shell, containment and applets
Url:            https://invent.kde.org/plasma/plasma-mobile
Source0:        https://download.kde.org/%{stable_kf6}/plasma/%{version}/plasma-mobile-%{version}.tar.xz
Source1:        https://download.kde.org/%{stable_kf6}/plasma/%{version}/plasma-mobile-%{version}.tar.xz.sig

#Source15:       fedora-lookandfeel.json

## upstream patches

## downstream patches
#Patch1001:      plasma-mobile-load-fedora-wallpaper.patch
#Patch1002:      plasma-mobile-select-fedora-lookandfeel.patch
Patch1003:      overrides.patch

# Remove the 'bugfix' digit from the version for some runtime requirements
%global plasma_version %(echo %{version} | cut -d. -f1-3)

BuildRequires: extra-cmake-modules
BuildRequires: gcc-c++
BuildRequires: kf6-kdbusaddons-devel
BuildRequires: kwin-devel
BuildRequires: qt6-qtdeclarative-devel
BuildRequires: desktop-file-utils
BuildRequires: libappstream-glib
BuildRequires: pkgconfig(libudev)
BuildRequires: pkgconfig(libdrm)

BuildRequires: cmake(KF6Auth)
BuildRequires: cmake(KF6Bookmarks)
BuildRequires: cmake(KF6Codecs)
BuildRequires: cmake(KF6Completion)
BuildRequires: cmake(KF6Config)
BuildRequires: cmake(KF6ConfigWidgets)
BuildRequires: cmake(KF6CoreAddons)
BuildRequires: cmake(KF6Declarative)
BuildRequires: cmake(KF6I18n)
BuildRequires: cmake(KF6ItemViews)
BuildRequires: cmake(KF6JobWidgets)
BuildRequires: cmake(KF6KCMUtils)
BuildRequires: cmake(KF6KIO)
BuildRequires: cmake(KF6KirigamiAddons)
BuildRequires: cmake(KF6ModemManagerQt)
BuildRequires: cmake(KF6NetworkManagerQt)
BuildRequires: cmake(KF6Notifications)
BuildRequires: cmake(KF6Package)
BuildRequires: cmake(KF6People)
BuildRequires: cmake(KF6Service)
BuildRequires: cmake(KF6Solid)
BuildRequires: cmake(KF6WidgetsAddons)
BuildRequires: cmake(KF6WindowSystem)
BuildRequires: cmake(KF6XmlGui)
BuildRequires: cmake(KF6ItemModels)
BuildRequires: cmake(KF6GlobalAccel)
BuildRequires: cmake(KF6Screen)
BuildRequires: cmake(KF6KirigamiPlatform)
BuildRequires: cmake(KPipeWire)
BuildRequires: cmake(Qt6Svg)
BuildRequires: cmake(Qt6Sensors)
BuildRequires: cmake(QCoro6)
BuildRequires: cmake(Qt6WaylandClient)
BuildRequires: cmake(libkworkspace)
BuildRequires: cmake(LayerShellQt)
BuildRequires: libepoxy-devel
BuildRequires: wayland-devel
BuildRequires: qt6-qtbase-private-devel

BuildRequires: cmake(PlasmaActivities)
BuildRequires: cmake(PlasmaWaylandProtocols)
BuildRequires: cmake(Plasma)
BuildRequires: cmake(KWayland)
BuildRequires: system-backgrounds-kde

# Requires: feedbackd
Requires: kf6-bluez-qt
Requires: kf6-kactivities
Requires: kf6-kdeclarative
Requires: kf6-kirigami2
Requires: kpipewire
# Plasma Mobile uses kscreen to automatically set a logical scaling factor based on hardware
Requires: kscreen
Requires: kwin
Requires: plasma-milou
Requires: plasma-nano
Requires: plasma-nm
Requires: plasma-pa
Requires: plasma-workspace >= %{plasma_version}
Requires: qqc2-breeze-style
Requires: qt6-qtwayland

# Default look-and-feel theme
#Requires: plasma-lookandfeel-fedora-mobile = %{version}-%{release}
Requires: system-backgrounds-kde

# This package now integrates what was plasma-nm-mobile
Obsoletes: plasma-nm-mobile < 5.27.81


%description
%{summary}.

#%package -n plasma-lookandfeel-fedora-mobile
#Summary:  Fedora look-and-feel for Plasma Mobile
#Requires: %{name} = %{version}-%{release}
#BuildArch: noarch
#%description -n plasma-lookandfeel-fedora-mobile
#%{summary}.


%prep
%autosetup -p1

# # Populate initial lookandfeel package
# cp -a lookandfeel lookandfeel-fedora
# # Overwrite settings to configure distro wallpaper
# sed -i -e 's|Image=Next$|Image=Default|' lookandfeel-fedora/contents/defaults
# install -m 0644 %{SOURCE15} lookandfeel-fedora/metadata.json
# cat >> CMakeLists.txt <<EOL
# plasma_install_package(lookandfeel-fedora org.fedoraproject.fedora.mobile look-and-feel lookandfeel)
# EOL
# 
# # RHEL 10 has .png, not .jxl
# if [ -e /usr/share/wallpapers/Default/contents/images/3840x2160.png ]; then
#   sed -e 's|\.jxl|.png|g' -i initialstart/qml/LandingComponent.qml
# fi

%build
%cmake_kf6
%cmake_build

%install
%cmake_install
%find_lang plasma_applet_org.kde.phone.homescreen --all-name

%check
appstream-util validate-relax --nonet %{buildroot}%{_kf6_metainfodir}/org.kde.plasma.mobileshell.metainfo.xml
desktop-file-validate %{buildroot}/%{_datadir}/applications/kcm_{mobile_info,mobile_time,mobileshell,navigation,waydroidintegration}.desktop

%files -f plasma_applet_org.kde.phone.homescreen.lang
%license LICENSES/*
%{_kf6_datadir}/plasma-mobile-device-presets/
%{_kf6_metainfodir}/org.kde.plasma.mobileshell.metainfo.xml
%{_kf6_libexecdir}/kauth/flashlighthelper
%{_kf6_libexecdir}/kauth/waydroidhelper
%{_kf6_bindir}/startplasmamobile
%{_kf6_bindir}/plasma-mobile-envmanager
%{_kf6_bindir}/plasma-mobile-initial-start
%{_kf6_datadir}/plasma/quicksettings
%{_kf6_datadir}/wayland-sessions/plasma-mobile.desktop
%{_kf6_datadir}/plasma/shells/org.kde.plasma.mobileshell
%{_kf6_datadir}/plasma-mobile-apn-info/apns-full-conf.xml
%{_kf6_datadir}/plasma/look-and-feel/org.kde.breeze.mobile
%{_kf6_datadir}/plasma/mobileinitialstart
%{_kf6_datadir}/applications/*.desktop
%{_kf6_datadir}/knotifications6/plasma_mobile_quicksetting*.notifyrc
%{_kf6_datadir}/qlogging-categories6/plasmamobile.categories
%{_kf6_datadir}/kwin/effects/mobiletaskswitcher
%{_kf6_datadir}/kwin/scripts/convergentwindows/contents/ui/main.qml
%{_kf6_datadir}/kwin/scripts/convergentwindows/metadata.json
%{_kf6_datadir}/plasma/layout-templates/org.kde.plasma.mobile.defaultNavigationPanel/contents/layout.js
%{_kf6_datadir}/plasma/layout-templates/org.kde.plasma.mobile.defaultNavigationPanel/metadata.json
%{_kf6_datadir}/plasma/layout-templates/org.kde.plasma.mobile.defaultStatusBar/contents/layout.js
%{_kf6_datadir}/plasma/layout-templates/org.kde.plasma.mobile.defaultStatusBar/metadata.json
%{_kf6_qmldir}/org/kde/plasma/private/mobileshell
%{_kf6_qmldir}/org/kde/plasma/quicksetting
%{_kf6_qmldir}/org/kde/plasma/mobileinitialstart
%{_kf6_qtplugindir}/plasma/kcms/systemsettings/kcm_navigation.so
%{_kf6_qtplugindir}/plasma/kcms/systemsettings/kcm_waydroidintegration.so
%{_datadir}/dbus-1/interfaces/org.kde.plasmashell*.xml
%{_datadir}/dbus-1/system-services/org.kde.plasma.mobileshell*.service
%{_datadir}/dbus-1/system.d/org.kde.plasma.mobileshell*.conf
%{_datadir}/polkit-1/actions/org.kde.plasma.mobileshell*.policy
%{_kf6_qtplugindir}/plasma/kcms/systemsettings/kcm_mobileshell.so
%{_kf6_qtplugindir}/plasma/applets/*.so
%{_kf6_qtplugindir}/kf6/kded/kded_plasma_mobile_start.so
%{_kf6_qtplugindir}/plasma/kcms/systemsettings/kcm_mobile_*.so
%{_kf6_qtplugindir}/kf6/kded/kded_plasma_mobile_autodetect_apn.so

#%files -n plasma-lookandfeel-fedora-mobile
#%{_kf6_datadir}/plasma/look-and-feel/org.fedoraproject.fedora.mobile

%changelog
* Tue Aug 04 2026 Steve Cossette <farchord@gmail.com> - 6.7.4-1
- 6.7.4

* Thu Jul 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 6.7.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_45_Mass_Rebuild

* Tue Jul 14 2026 Steve Cossette <farchord@gmail.com> - 6.7.3-1
- 6.7.3

* Wed Jul 01 2026 Steve Cossette <farchord@gmail.com> - 6.7.2-1
- 6.7.2

* Tue Jun 23 2026 Steve Cossette <farchord@gmail.com> - 6.7.1-1
- 6.7.1

* Thu Jun 11 2026 Steve Cossette <farchord@gmail.com> - 6.7.0-1
- 6.7.0

* Fri May 29 2026 Steve Cossette <farchord@gmail.com> - 6.6.91-1
- 6.6.91

* Sat May 16 2026 Steve Cossette <farchord@gmail.com> - 6.6.90-1
- 6.6.90

* Thu May 14 2026 Steve Cossette <farchord@gmail.com> - 6.6.5-1
- 6.6.5

* Thu May 14 2026 Jan Grulich <jgrulich@redhat.com> - 6.6.4-3
- Rebuild (qt6)

* Thu Apr 16 2026 Jan Grulich <jgrulich@redhat.com> - 6.6.4-2
- Rebuild (qt6)

* Fri Apr 10 2026 Steve Cossette <farchord@gmail.com> - 6.6.4-1
- 6.6.4

* Tue Mar 17 2026 Steve Cossette <farchord@gmail.com> - 6.6.3-1
- 6.6.3

* Tue Mar 03 2026 Steve Cossette <farchord@gmail.com> - 6.6.2-1
- 6.6.2

* Tue Feb 24 2026 Steve Cossette <farchord@gmail.com> - 6.6.1-1
- 6.6.1

* Thu Feb 12 2026 Steve Cossette <farchord@gmail.com> - 6.6.0-1
- 6.6.0

* Tue Jan 27 2026 Steve Cossette <farchord@gmail.com> - 6.5.91-1
- 6.5.91

* Mon Jan 19 2026 Yaakov Selkowitz <yselkowi@redhat.com> - 6.5.90-3
- Add Fedora look-and-feel for mobile

* Sat Jan 17 2026 Fedora Release Engineering <releng@fedoraproject.org> - 6.5.90-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Tue Jan 13 2026 farchord@gmail.com - 6.5.90-1
- 6.5.90

* Tue Jan 13 2026 farchord@gmail.com - 6.5.5-1
- 6.5.5

* Tue Dec 09 2025 Steve Cossette <farchord@gmail.com> - 6.5.4-1
- 6.5.4

* Tue Nov 18 2025 Steve Cossette <farchord@gmail.com> - 6.5.3-1
- 6.5.3

* Tue Nov 04 2025 Steve Cossette <farchord@gmail.com> - 6.5.2-1
- 6.5.2

* Tue Oct 28 2025 Steve Cossette <farchord@gmail.com> - 6.5.1-1
- 6.5.1

* Fri Oct 17 2025 Steve Cossette <farchord@gmail.com> - 6.5.0-1
- 6.5.0

* Thu Oct 02 2025 Steve Cossette <farchord@gmail.com> - 6.4.91-1
- 6.4.91

* Tue Sep 30 2025 Jan Grulich <jgrulich@redhat.com> - 6.4.5-2
- Rebuild (qt6)

* Thu Sep 25 2025 Steve Cossette <farchord@gmail.com> - 6.4.90-1
- 6.4.90

* Tue Sep 16 2025 farchord@gmail.com - 6.4.5-1
- 6.4.5

* Sat Aug 16 2025 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.4.4-2
- Drop i686 support (leaf package)

* Wed Aug 06 2025 Steve Cossette <farchord@gmail.com> - 6.4.4-1
- 6.4.4

* Fri Jul 25 2025 Fedora Release Engineering <releng@fedoraproject.org> - 6.4.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Tue Jul 15 2025 Steve Cossette <farchord@gmail.com> - 6.4.3-1
- 6.4.3

* Thu Jul 03 2025 Steve Cossette <farchord@gmail.com> - 6.4.2-1
- 6.4.2

* Tue Jun 24 2025 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.4.1-1
- 6.4.1

* Mon Jun 16 2025 Steve Cossette <farchord@gmail.com> - 6.4.0-1
- 6.4.0

* Sat May 31 2025 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.3.91-2
- Add signature file

* Fri May 30 2025 Steve Cossette <farchord@gmail.com> - 6.3.91-1
- 6.3.91

* Thu May 15 2025 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.3.90-1
- 6.3.90

* Tue May 06 2025 Steve Cossette <farchord@gmail.com> - 6.3.5-1
- 6.3.5

* Mon Apr 14 2025 Jan Grulich <jgrulich@redhat.com> - 6.3.4-2
- Rebuild (qt6)

* Wed Apr 02 2025 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.3.4-1
- 6.3.4

* Tue Mar 25 2025 Jan Grulich <jgrulich@redhat.com> - 6.3.3-2
- Rebuild (qt6)

* Tue Mar 11 2025 Steve Cossette <farchord@gmail.com> - 6.3.3-1
- 6.3.3

* Tue Feb 25 2025 Steve Cossette <farchord@gmail.com> - 6.3.2-1
- 6.3.2

* Tue Feb 18 2025 Steve Cossette <farchord@gmail.com> - 6.3.1-1
- 6.3.1

* Thu Feb 06 2025 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.3.0-1
- 6.3.0

* Thu Jan 23 2025 Steve Cossette <farchord@gmail.com> - 6.2.91-1
- 6.2.91

* Sat Jan 18 2025 Fedora Release Engineering <releng@fedoraproject.org> - 6.2.90-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Thu Jan 09 2025 Steve Cossette <farchord@gmail.com> - 6.2.90-1
- Beta 6.2.90

* Tue Dec 31 2024 Steve Cossette <farchord@gmail.com> - 6.2.5-1
- 6.2.5

* Tue Nov 26 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.2.4-1
- 6.2.4

* Tue Nov 05 2024 Steve Cossette <farchord@gmail.com> - 6.2.3-1
- 6.2.3

* Tue Oct 22 2024 Steve Cossette <farchord@gmail.com> - 6.2.2-1
- 6.2.2

* Tue Oct 15 2024 Steve Cossette <farchord@gmail.com> - 6.2.1-1
- 6.2.1

* Thu Oct 03 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.2.0-1
- 6.2.0

* Thu Sep 12 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.1.90-1
- 6.1.90

* Tue Sep 10 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.1.5-1
- 6.1.5

* Fri Aug 09 2024 Steve Cossette <farchord@gmail.com> - 6.1.4-1
- 6.1.4

* Wed Jul 24 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.1.3-3
- rebuilt

* Fri Jul 19 2024 Fedora Release Engineering <releng@fedoraproject.org> - 6.1.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Tue Jul 16 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.1.3-1
- 6.1.3

* Wed Jul 03 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.1.2-1
- 6.1.2

* Tue Jun 25 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.1.1-1
- 6.1.1

* Thu Jun 13 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.1.0-1
- 6.1.0

* Fri May 24 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.0.90-1
- 6.0.90

* Wed May 22 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.0.5-1
- 6.0.5

* Tue Apr 16 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.0.4-1
- 6.0.4

* Tue Apr 09 2024 Troy Dawson <tdawson@redhat.com> - 6.0.3.1-3
- Fix the runtime requirement versioning fix

* Tue Apr 02 2024 Steve Cossette <farchord@gmail.com> - 6.0.3.1-2
- Fixed an issue with runtime requirement versioning

* Wed Mar 27 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.0.3.1-1
- 6.0.3.1

* Tue Mar 26 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.0.3-1
- 6.0.3

* Tue Mar 12 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.0.2-1
- 6.0.2

* Wed Mar 06 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.0.1-1
- 6.0.1

* Wed Feb 21 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 6.0.0-1
- 6.0.0

* Wed Jan 31 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 5.93.0-1
- 5.93.0

* Thu Jan 25 2024 Fedora Release Engineering <releng@fedoraproject.org> - 5.92.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Sun Jan 21 2024 Fedora Release Engineering <releng@fedoraproject.org> - 5.92.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Wed Jan 10 2024 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 5.92.0-1
- 5.92.0

* Thu Dec 21 2023 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 5.91.0-1
- 5.91.0

* Sun Dec 03 2023 Justin Zobel <justin.zobel@gmail.com> - 5.90.0-1
- Update to 5.90.0

* Fri Nov 24 2023 Steve Cossette <farchord@gmail.com> - 5.27.80-1
- 5.27.80

* Tue Oct 24 2023 Steve Cossette <farchord@gmail.com> - 5.27.9-1
- 5.27.9

* Tue Sep 12 2023 justin.zobel@gmail.com - 5.27.8-1
- 5.27.8

* Tue Aug 01 2023 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 5.27.7-1
- 5.27.7

* Fri Jul 21 2023 Fedora Release Engineering <releng@fedoraproject.org> - 5.27.6-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Sun Jun 25 2023 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 5.27.6-1
- 5.27.6

* Tue May 16 2023 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 5.27.5-1
- 5.27.5

* Tue Apr 04 2023 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 5.27.4-1
- 5.27.4

* Tue Mar 14 2023 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 5.27.3-1
- 5.27.3

* Tue Feb 28 2023 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 5.27.2-1
- 5.27.2

* Tue Feb 21 2023 Marc Deop i Argemí <marcdeop@fedoraproject.org> - 5.27.1-1
- 5.27.1

* Thu Feb 09 2023 Marc Deop <marcdeop@fedoraproject.org> - 5.27.0-1
- 5.27.0

* Fri Jan 20 2023 Fedora Release Engineering <releng@fedoraproject.org> - 5.26.90-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Thu Jan 19 2023 Marc Deop <marcdeop@fedoraproject.org> - 5.26.90-1
- 5.26.90

* Sat Jan 07 2023 Marc Deop <marcdeop@fedoraproject.org> - 5.26.5-1
- 5.26.5

* Tue Nov 29 2022 Marc Deop <marcdeop@fedoraproject.org> - 5.26.4-1
- 5.26.4

* Wed Nov 09 2022 Marc Deop <marcdeop@fedoraproject.org> - 5.26.3-1
- 5.26.3

* Wed Oct 26 2022 Marc Deop <marcdeop@fedoraproject.org> - 5.26.2-1
- 5.26.2

* Tue Oct 18 2022 Marc Deop <marcdeop@fedoraproject.org> - 5.26.1-1
- 5.26.1

* Thu Oct 06 2022 Marc Deop <marcdeop@fedoraproject.org> - 5.26.0-1
- 5.26.0

* Sat Sep 17 2022 Marc Deop <marcdeop@fedoraproject.org> - 5.25.90-1
- 5.25.90

* Wed Sep 07 2022 Marc Deop <marcdeop@fedoraproject.org> - 5.25.5-1
- 5.25.5

* Sat Mar 19 2022 Justin Zobel <justin@1707.io> - 5.24.3
- Update to 5.24.3

* Fri Feb 18 2022 Justin Zobel <justin@1707.io> - 5.24.1
- Initial version of package
