
%global qt6_minver 6.6.0
%global kf6_minver 6.5.0
 
%global orgname org.kde.plasmasetup
 
# https://docs.fedoraproject.org/en-US/packaging-guidelines/#_compiler_flags
%global _hardened_build 1
 
Name:           plasma-setup
Version:        6.7.4
Release:        1%{?dist}
Summary:        Initial setup for systems using KDE Plasma
License:        (GPL-2.0-or-later or GPL-3.0-or-later) and GPL-2.0-or-later and GPL-3.0-or-later and (LGPL-2.0-or-later or LGPL-3.0-or-later) and (LGPL-2.1-or-later or LGPL-3.0-or-later) and LGPL-2.1-or-later and BSD-2-Clause and CC0-1.0
URL:            https://invent.kde.org/plasma/%{name}
 
Source0: http://download.kde.org/%{stable_kf6}/plasma/%{maj_ver_kf6}.%{min_ver_kf6}.%{bug_ver_kf6}/%{name}-%{version}.tar.xz
Source1: http://download.kde.org/%{stable_kf6}/plasma/%{maj_ver_kf6}.%{min_ver_kf6}.%{bug_ver_kf6}/%{name}-%{version}.tar.xz.sig
 
# Backported changes
 
# Proposed changes
 
# Downstream only changes
Patch1001:      plasma-setup-load-default-wallpaper.patch
Patch1002:      plasma-setup-select-fedora-lookandfeel.patch
Patch1003:      overrides.patch
 
BuildRequires:  cmake(Qt6Core) >= %{qt6_minver}
BuildRequires:  cmake(Qt6Gui) >= %{qt6_minver}
BuildRequires:  cmake(Qt6Qml) >= %{qt6_minver}
BuildRequires:  cmake(Qt6QuickControls2) >= %{qt6_minver}
BuildRequires:  cmake(Qt6Svg) >= %{qt6_minver}
BuildRequires:  cmake(Qt6Widgets) >= %{qt6_minver}
BuildRequires:  cmake(Qt6DBus) >= %{qt6_minver}
BuildRequires:  cmake(KF6I18n) >= %{kf6_minver}
BuildRequires:  cmake(KF6Package) >= %{kf6_minver}
BuildRequires:  cmake(KF6Auth) >= %{kf6_minver}
BuildRequires:  cmake(KF6CoreAddons) >= %{kf6_minver}
BuildRequires:  cmake(KF6Config) >= %{kf6_minver}
BuildRequires:  cmake(KF6Screen)
BuildRequires:  cmake(LibKWorkspace)
BuildRequires:  cracklib-devel
BuildRequires:  extra-cmake-modules >= %{kf6_minver}
BuildRequires:  gcc-c++
BuildRequires:  git-core
BuildRequires:  systemd-rpm-macros
BuildRequires:  kf6-rpm-macros
BuildRequires:  libappstream-glib
BuildRequires:  system-backgrounds-kde
BuildRequires:  qt6qml(org.kde.plasma.private.kcm_keyboard)
 
Requires:       qt6qml(org.kde.plasma.private.kcm_keyboard)
 
Requires:       dbus-common
Requires:       kf6-filesystem
Requires:       kf6-kauth
 
# Require plasma-lookandfeel-fedora with light/dark themes
Requires:       plasma-lookandfeel-fedora >= 6.5.3-3
Requires:       system-backgrounds-kde
 
# Renamed from KDE Initial System Setup / kiss
Obsoletes:      kiss < %{version}-%{release}
Provides:       kiss = %{version}-%{release}
Provides:       kiss%{?_isa} = %{version}-%{release}
 
# https://fedoraproject.org/wiki/Changes/EncourageI686LeafRemoval
ExcludeArch:    %{ix86}
 
# Do not check .so files in an application-specific library directory
%global __provides_exclude_from ^%{_kf6_qmldir}/org/kde/plasmasetup/.*\\.so.*$
 
 
%description
%{summary}.
 
 
%prep
%autosetup -p1
# e.g. RHEL 10 has .png, not .jxl
if [ -f /usr/share/wallpapers/Default/contents/images/5120x2880.png ]; then
sed -i -e 's|\.jxl|.png|' src/qml/LandingComponent.qml
fi
 
 
%build
%cmake_kf6
%cmake_build
 
%install
%cmake_install
%find_lang %{orgname} --all-name
rm -fv %{buildroot}%{_kf6_libdir}/libcomponentspluginplugin.a
 
 
%preun
%systemd_preun %{name}.service
 
 
%post
%systemd_post %{name}.service
 
 
%postun
%systemd_postun %{name}.service
 
 
%triggerun -- fedora-release-common < 44
# When upgrading to Fedora 44, mark the system as configured if /etc/reconfigSys doesn't exist
if [ ! -f "%{_sysconfdir}/reconfigSys" ]; then
   touch %{_sysconfdir}/plasma-setup-done
fi
exit 0
 
 
%files -f %{orgname}.lang
%license LICENSES/*
%config(noreplace) %{_sysconfdir}/xdg/plasmasetuprc
%{_libexecdir}/%{name}*
%{_kf6_libexecdir}/kauth/%{name}*
%{_kf6_qmldir}/org/kde/plasmasetup/
%{_kf6_plugindir}/packagestructure/plasmasetup.so
%{_kf6_datadir}/plasma/packages/%{orgname}.*/
%license %{_kf6_datadir}/plasma/packages/%{orgname}.finished/contents/ui/konqi-calling.png.license
%{_unitdir}/%{name}*
%{_sysusersdir}/%{name}*
%{_tmpfilesdir}/%{name}*
%{_datadir}/dbus-1/*/%{orgname}.*
%{_datadir}/polkit-1/actions/%{orgname}.*
%{_datadir}/polkit-1/rules.d/%{name}*
%{_datadir}/qlogging-categories6/plasmasetup.categories
%{_datadir}/%{name}/
 
 
%changelog
* Tue Aug 04 2026 Steve Cossette <farchord@gmail.com> - 6.7.4-1
- 6.7.4

* Tue Jul 28 2026 Adam Williamson <awilliam@redhat.com> - 6.7.3-4
- Revert MR #109 backport (it causes a regression)

* Wed Jul 22 2026 Adam Williamson <awilliam@redhat.com> - 6.7.3-3
- Backport MR #109 to fix language search

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
 
* Sat May 23 2026 Steve Cossette <farchord@gmail.com> - 6.6.90-1
- 6.6.90
 
* Thu May 21 2026 Adam Williamson <awilliam@redhat.com> - 6.6.5-2
- Re-backport MR #101 to pre-select configured keyboard layout (#2453216)
 
* Thu May 14 2026 Steve Cossette <farchord@gmail.com> - 6.6.5-1
- 6.6.5
 
* Thu May 14 2026 Jan Grulich <jgrulich@redhat.com> - 6.6.4-7
- Rebuild (qt6)
 
* Sun Apr 19 2026 Adam Williamson <awilliam@redhat.com> - 6.6.4-6
- Backport MR #101 to pre-select configured keyboard layout (#2453216)
 
* Fri Apr 17 2026 Jan Grulich <jgrulich@redhat.com> - 6.6.4-5
- Rebuild (qt6)
 
* Tue Apr 14 2026 Adam Williamson <awilliam@redhat.com> - 6.6.4-4
- Drop MR #99 backport, it's broken (desktop doesn't load right)
 
* Tue Apr 14 2026 Adam Williamson <awilliam@redhat.com> - 6.6.4-3
- Backport MR #99 to fix launcher icon when selecting dark mode
- Backport MR #100 to maybe fix strange behavior in wifi page
 
* Tue Apr 14 2026 Adam Williamson <awilliam@redhat.com> - 6.6.4-2
- Backport MR #98 to fix system-wide network connection creation
 
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
 
* Sat Feb 07 2026 Neal Gompa <ngompa@fedoraproject.org> - 6.5.91-2
- Update trigger to fire on system upgrade of fedora-release-common
 
* Tue Jan 27 2026 Steve Cossette <farchord@gmail.com> - 6.5.91-1
- 6.5.91
 
* Mon Jan 19 2026 Yaakov Selkowitz <yselkowi@redhat.com> - 6.5.90-3
- Use system-backgrounds-kde for wallpaper
 
* Sat Jan 17 2026 Fedora Release Engineering <releng@fedoraproject.org> - 6.5.90-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild
 
* Tue Jan 13 2026 farchord@gmail.com - 6.5.90-1
- 6.5.90
 
* Mon Jan 12 2026 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20260112gitc46bd5f-1
- Bump to new git snapshot
 
* Sun Jan 11 2026 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20260110git1524a42-1
- Bump to new git snapshot
 
* Tue Jan 06 2026 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20260105git81df938-2
- Add trigger scriptlet to disable plasma-setup for upgrades to F44
 
* Mon Jan 05 2026 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20260105git81df938-1
- Bump to new git snapshot
 
* Sat Jan 03 2026 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20251218git359ce87-2
- Add patch to support setting the hostname
 
* Thu Dec 18 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20251218git359ce87-1
- Bump to new git snapshot
 
* Mon Dec 15 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20251215git7f24516-1
- Bump to new git snapshot
 
* Mon Dec 08 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20251208git9ee3322-1
- Bump to new git snapshot
- Drop merged patch for existing users check
 
* Mon Dec 08 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20251205gitd520c0e-4
- Refresh patch again for existing users check
 
* Mon Dec 08 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20251205gitd520c0e-3
- Refresh patch for existing users check
 
* Sun Dec 07 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20251205gitd520c0e-2
- Add patch to fix uid check to correctly detect existing users
 
* Fri Dec 05 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20251205gitd520c0e-1
- Bump to new git snapshot
- Add patches to correctly handle fedora look and feel setup
 
* Tue Dec 02 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20251201gitb8bc623-1
- Bump to new git snapshot
- Add patch to handle existing users on firstboot setup
 
* Sun Nov 30 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20251130git84b5d3c-1
- Bump to new git snapshot
 
* Tue Nov 25 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20251123git180844b-2
- Add patch to change self-disable behavior to use a flag file
 
* Mon Nov 24 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20251123git180844b-1
- Bump to new git snapshot
 
* Sat Sep 27 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20250926giteeeb5a1-1
- Bump to new git snapshot
- Rename to plasma-setup
 
* Sun Sep 07 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20250906git69c6007-2
- Drop i686 support as required dependencies are no longer available
 
* Sat Sep 06 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20250906git69c6007-1
- Bump to new git snapshot
 
* Thu Jul 24 2025 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.0~20250524gitade7962-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild
 
* Mon May 26 2025 Neal Gompa <ngompa@fedoraproject.org> - 0.1.0~20250524gitade7962-1
- Rebase to new rewrite
 
* Fri Jan 17 2025 Fedora Release Engineering <releng@fedoraproject.org> - 0~20211207git22cf331-10
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild
 
* Mon Jul 29 2024 Miroslav SuchÃ½ <msuchy@redhat.com> - 0~20211207git22cf331-9
- convert license to SPDX
 
* Thu Jul 18 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0~20211207git22cf331-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild
 
* Thu Jan 25 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0~20211207git22cf331-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild
 
* Sun Jan 21 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0~20211207git22cf331-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild
 
* Thu Jul 20 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0~20211207git22cf331-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild
 
* Thu Jan 19 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0~20211207git22cf331-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild
 
* Thu Jul 21 2022 Fedora Release Engineering <releng@fedoraproject.org> - 0~20211207git22cf331-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_37_Mass_Rebuild
 
* Thu Jan 20 2022 Fedora Release Engineering <releng@fedoraproject.org> - 0~20211207git22cf331-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_36_Mass_Rebuild
 
* Tue Dec 07 2021 Marc Deop <marcdeop@fedoraproject.org> - 0~20211207git22cf331-1
- Initial Release
