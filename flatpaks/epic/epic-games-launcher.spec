%global debug_package %{nil}
# The AppImage is an immutable bootstrap payload, not an RPM-managed ELF binary.
%global __brp_strip %{nil}
%global __brp_strip_comment_note %{nil}
%global __requires_exclude_from ^%{_datadir}/epic-games-launcher/.*$
%global __provides_exclude_from ^%{_datadir}/epic-games-launcher/.*$
%global appstream_id org.anatase.EpicGamesLauncher
%global upstream_commit g6aa6663
%global seed_sha256 946993bc8c9c9d16e87035c964bd706272c35b5f0486498ec5b707be0db1a578

Name:           anatase-epic-games-launcher
Version:        0.102.0
Release:        1%{?dist}
Summary:        Self-updating Epic Games Launcher
License:        LicenseRef-proprietary
URL:            https://www.launcher.epicgames.com/
ExclusiveArch:  x86_64

Source0:        https://content-download-egs.distro.on.epicgames.com/Builds/EGLv2/%{version}%%2B%{upstream_commit}/Linux/EpicGamesLauncher-x86_64.AppImage
Source1:        anatase-epic-games-launcher
Source2:        test-anatase-epic-games-launcher.py
Source3:        %{appstream_id}.metainfo.xml

BuildRequires:  bash
BuildRequires:  coreutils
BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib
BuildRequires:  python3
BuildRequires:  util-linux
Requires:       bash
Requires:       coreutils
Requires:       util-linux
Requires:       xdg-utils

%description
Epic Games Launcher packaged with a private, writable AppImage. The bundled
AppImage initializes each user's installation once and Epic's updater manages
subsequent application updates inside the Flatpak sandbox.

%prep
%setup -q -c -T
echo '%{seed_sha256}  %{SOURCE0}' | sha256sum --check --strict
install -m0755 %{SOURCE0} bootstrap.AppImage
# Build artifacts and extraction must stay on disk, including in containers.
mkdir -p tmp
TMPDIR="$PWD/tmp" ./bootstrap.AppImage --appimage-extract > /dev/null

%build
# The upstream application is shipped prebuilt.

%install
install -Dm0644 %{SOURCE0} %{buildroot}%{_datadir}/epic-games-launcher/EpicGamesLauncher-x86_64.AppImage
install -Dm0755 %{SOURCE1} %{buildroot}%{_bindir}/anatase-epic-games-launcher

desktop=squashfs-root/usr/share/applications/epic-games-launcher.desktop
sed \
    -e 's|^Exec=.*|Exec=anatase-epic-games-launcher %%u|' \
    -e 's|^Icon=.*|Icon=%{appstream_id}|' \
    "$desktop" > %{appstream_id}.desktop
desktop-file-edit --set-key=Comment --set-value='Play games from the Epic Games store' %{appstream_id}.desktop
install -Dm0644 %{appstream_id}.desktop %{buildroot}%{_datadir}/applications/%{appstream_id}.desktop
for size in 32x32 128x128 256x256@2; do
    install -Dm0644 "squashfs-root/usr/share/icons/hicolor/$size/apps/EpicGamesLauncher.png" \
        "%{buildroot}%{_datadir}/icons/hicolor/$size/apps/%{appstream_id}.png"
done
install -Dm0644 %{SOURCE3} %{buildroot}%{_metainfodir}/%{appstream_id}.metainfo.xml
rm -rf -- bootstrap.AppImage squashfs-root

%check
export TMPDIR="$PWD/tmp"
bash -n %{buildroot}%{_bindir}/anatase-epic-games-launcher
ANATASE_EPIC_LAUNCHER=%{buildroot}%{_bindir}/anatase-epic-games-launcher python3 %{SOURCE2}
desktop-file-validate %{buildroot}%{_datadir}/applications/%{appstream_id}.desktop
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/%{appstream_id}.metainfo.xml
echo '%{seed_sha256}  %{buildroot}%{_datadir}/epic-games-launcher/EpicGamesLauncher-x86_64.AppImage' | sha256sum --check --strict

%files
%{_bindir}/anatase-epic-games-launcher
%{_datadir}/epic-games-launcher/
%{_datadir}/applications/%{appstream_id}.desktop
%{_datadir}/icons/hicolor/*/apps/%{appstream_id}.png
%{_metainfodir}/%{appstream_id}.metainfo.xml
