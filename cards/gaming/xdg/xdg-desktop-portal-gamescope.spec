%global commit 412a4bff892bdb5726a549d03b11e6ce2f8e8152
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global rust_systemd_journal_logger_ver 2.2.2
%global rust_xdg_user_ver 0.2.1
%global rust_home_ver 0.5.12

Name:           xdg-desktop-portal-gamescope
Version:        0.1.33.%{shortcommit}
Release:        %autorelease
Summary:        Gamescope-specific backend for xdg-desktop-portal

License:        BSD-3-Clause
URL:            https://github.com/evlav/xdg-desktop-portal-gamescope
Source0:        %{url}/archive/%{commit}/%{name}-%{shortcommit}.tar.gz
Source1:        https://crates.io/api/v1/crates/systemd-journal-logger/%{rust_systemd_journal_logger_ver}/download#/systemd-journal-logger-%{rust_systemd_journal_logger_ver}.tar.gz
Source2:        https://crates.io/api/v1/crates/xdg-user/%{rust_xdg_user_ver}/download#/xdg-user-%{rust_xdg_user_ver}.tar.gz
Source3:        https://crates.io/api/v1/crates/home/%{rust_home_ver}/download#/home-%{rust_home_ver}.tar.gz
Patch0:         overrides.patch

BuildRequires:  cargo
BuildRequires:  cargo-rpm-macros >= 26
BuildRequires:  meson
BuildRequires:  rust
BuildRequires:  rust-packaging
BuildRequires:  rust-std-static
BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(systemd)
BuildRequires:  (crate(ashpd/backend) >= 0.13.9 with crate(ashpd/backend) < 0.14.0~)
BuildRequires:  (crate(ashpd/screencast) >= 0.13.9 with crate(ashpd/screencast) < 0.14.0~)
BuildRequires:  (crate(ashpd/screenshot) >= 0.13.9 with crate(ashpd/screenshot) < 0.14.0~)
BuildRequires:  (crate(async-trait/default) >= 0.1.89 with crate(async-trait/default) < 0.2.0~)
BuildRequires:  (crate(chrono/default) >= 0.4.44 with crate(chrono/default) < 0.5.0~)
BuildRequires:  (crate(futures-util/default) >= 0.3.32 with crate(futures-util/default) < 0.4.0~)
BuildRequires:  (crate(inotify/default) >= 0.11.1 with crate(inotify/default) < 0.12.0~)
BuildRequires:  (crate(log/default) >= 0.4.29 with crate(log/default) < 0.5.0~)
BuildRequires:  (crate(tokio/fs) >= 1.50.0 with crate(tokio/fs) < 2.0.0~)
BuildRequires:  (crate(tokio/macros) >= 1.50.0 with crate(tokio/macros) < 2.0.0~)
BuildRequires:  (crate(tokio/net) >= 1.50.0 with crate(tokio/net) < 2.0.0~)
BuildRequires:  (crate(tokio/process) >= 1.50.0 with crate(tokio/process) < 2.0.0~)
BuildRequires:  (crate(tokio/rt-multi-thread) >= 1.50.0 with crate(tokio/rt-multi-thread) < 2.0.0~)
BuildRequires:  (crate(tokio/sync) >= 1.50.0 with crate(tokio/sync) < 2.0.0~)
BuildRequires:  (crate(wayland-backend/default) >= 0.3.14 with crate(wayland-backend/default) < 0.4.0~)
BuildRequires:  (crate(wayland-client/default) >= 0.31.13 with crate(wayland-client/default) < 0.32.0~)
BuildRequires:  (crate(wayland-scanner/default) >= 0.31.9 with crate(wayland-scanner/default) < 0.32.0~)

Requires:       gamescope
Provides:       xdg-desktop-portal-impl

%description
%{name} implements Access, ScreenCast, and Screenshot portal interfaces by
communicating with the Gamescope compositor.

%prep
%autosetup -p1 -n %{name}-%{commit}

# The package does not run or ship the upstream integration tests. Removing
# their manifest section also keeps Cargo's offline resolver from requiring
# test-only crates during a release build.
sed -i '/^\[dev-dependencies\]/,$d' Cargo.toml
sed -i "/subdir('tests')/d" meson.build

mkdir -p vendor
tar -xf %{SOURCE1} -C vendor
tar -xf %{SOURCE2} -C vendor
tar -xf %{SOURCE3} -C vendor
# Cargo still resolves target-specific dependencies in offline mode. The
# Windows-only dependency is neither built nor available in Fedora's registry.
sed -i '/^\[target\."cfg(windows)"\.dependencies\.windows-sys\]/,/^$/d' \
  vendor/home-%{rust_home_ver}/Cargo.toml

%cargo_prep
cat >> .cargo/config.toml << EOF

[patch.crates-io]
systemd-journal-logger = { path = "vendor/systemd-journal-logger-%{rust_systemd_journal_logger_ver}" }
xdg-user = { path = "vendor/xdg-user-%{rust_xdg_user_ver}" }
home = { path = "vendor/home-%{rust_home_ver}" }
EOF

%build
%meson
%meson_build
%{cargo_license_summary}
%{cargo_license} > LICENSE.dependencies

%install
%meson_install

%files
%license LICENSE LICENSE.dependencies
%doc README.md
%{_libexecdir}/xdg-desktop-portal-gamescope
%{_datadir}/applications/xdg-desktop-portal-gamescope.desktop
%{_datadir}/dbus-1/services/org.freedesktop.impl.portal.desktop.gamescope.service
%{_datadir}/xdg-desktop-portal/gamescope-portals/gamescope.portal
%{_userunitdir}/xdg-desktop-portal-gamescope.service

%changelog
%autochangelog
