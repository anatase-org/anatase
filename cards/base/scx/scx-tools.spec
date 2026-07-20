%define _disable_source_fetch 0

# prevent library files from being installed
%global cargo_install_lib 0

# Disable debug package generation
%global debug_package %{nil}

Name:           scx-tools
Version:        1.1.2
Release:        1%{?dist}
Summary:        Sched_ext Tools

License:        GPL=2.0
URL:            https://github.com/sched-ext/scx-loader
Source0:        %{URL}/archive/refs/tags/v%{version}.tar.gz
%global rust_clap_ver 4.6.1
%global rust_clap_builder_ver 4.6.0
%global rust_clap_derive_ver 4.6.1
%global rust_endi_ver 1.1.1
%global rust_ordered_stream_ver 0.2.0
%global rust_sysinfo_ver 0.38.4
%global rust_tokio_ver 1.52.3
%global rust_tokio_macros_ver 2.7.0
%global rust_zbus_ver 5.15.0
%global rust_zbus_macros_ver 5.15.0
%global rust_zbus_names_ver 4.3.2
%global rust_zbus_polkit_ver 5.0.0
%global rust_zvariant_ver 5.11.0
%global rust_zvariant_derive_ver 5.11.0
%global rust_zvariant_utils_ver 3.3.1
Source10:       https://crates.io/api/v1/crates/sysinfo/%{rust_sysinfo_ver}/download#/sysinfo-%{rust_sysinfo_ver}.tar.gz
Source11:       https://crates.io/api/v1/crates/clap/%{rust_clap_ver}/download#/clap-%{rust_clap_ver}.tar.gz
Source12:       https://crates.io/api/v1/crates/clap_derive/%{rust_clap_derive_ver}/download#/clap_derive-%{rust_clap_derive_ver}.tar.gz
Source13:       https://crates.io/api/v1/crates/endi/%{rust_endi_ver}/download#/endi-%{rust_endi_ver}.tar.gz
Source14:       https://crates.io/api/v1/crates/ordered-stream/%{rust_ordered_stream_ver}/download#/ordered-stream-%{rust_ordered_stream_ver}.tar.gz
Source15:       https://crates.io/api/v1/crates/clap_builder/%{rust_clap_builder_ver}/download#/clap_builder-%{rust_clap_builder_ver}.tar.gz
Source18:       https://crates.io/api/v1/crates/tokio/%{rust_tokio_ver}/download#/tokio-%{rust_tokio_ver}.tar.gz
Source19:       https://crates.io/api/v1/crates/tokio-macros/%{rust_tokio_macros_ver}/download#/tokio-macros-%{rust_tokio_macros_ver}.tar.gz
Source20:       https://crates.io/api/v1/crates/zbus/%{rust_zbus_ver}/download#/zbus-%{rust_zbus_ver}.tar.gz
Source21:       https://crates.io/api/v1/crates/zbus_macros/%{rust_zbus_macros_ver}/download#/zbus_macros-%{rust_zbus_macros_ver}.tar.gz
Source22:       https://crates.io/api/v1/crates/zbus_names/%{rust_zbus_names_ver}/download#/zbus_names-%{rust_zbus_names_ver}.tar.gz
Source23:       https://crates.io/api/v1/crates/zbus_polkit/%{rust_zbus_polkit_ver}/download#/zbus_polkit-%{rust_zbus_polkit_ver}.tar.gz
Source24:       https://crates.io/api/v1/crates/zvariant/%{rust_zvariant_ver}/download#/zvariant-%{rust_zvariant_ver}.tar.gz
Source25:       https://crates.io/api/v1/crates/zvariant_derive/%{rust_zvariant_derive_ver}/download#/zvariant_derive-%{rust_zvariant_derive_ver}.tar.gz
Source26:       https://crates.io/api/v1/crates/zvariant_utils/%{rust_zvariant_utils_ver}/download#/zvariant_utils-%{rust_zvariant_utils_ver}.tar.gz

BuildRequires:  gcc
BuildRequires:  git
BuildRequires:  python
BuildRequires:  cargo-rpm-macros >= 26
BuildRequires:  cargo
BuildRequires:  rust
BuildRequires:  rust-packaging
BuildRequires:  rust-std-static
BuildRequires:  clang >= 17
BuildRequires:  llvm >= 17
BuildRequires:  lld >= 17
BuildRequires:  systemd
BuildRequires:  bpftool
BuildRequires:  libseccomp-devel
BuildRequires:  (crate(anyhow/default) >= 1.0.102 with crate(anyhow/default) < 2.0.0~)
BuildRequires:  (crate(clap/default) >= 4.5.0 with crate(clap/default) < 5.0.0~)
BuildRequires:  (crate(clap/derive) >= 4.5.0 with crate(clap/derive) < 5.0.0~)
BuildRequires:  (crate(clap/env) >= 4.5.0 with crate(clap/env) < 5.0.0~)
BuildRequires:  (crate(clap/unicode) >= 4.5.0 with crate(clap/unicode) < 5.0.0~)
BuildRequires:  (crate(clap/wrap_help) >= 4.5.0 with crate(clap/wrap_help) < 5.0.0~)
BuildRequires:  (crate(colored/default) >= 3.1.1 with crate(colored/default) < 4.0.0~)
BuildRequires:  (crate(ctrlc/default) >= 3.5.0 with crate(ctrlc/default) < 4.0.0~)
BuildRequires:  (crate(ctrlc/termination) >= 3.5.0 with crate(ctrlc/termination) < 4.0.0~)
BuildRequires:  (crate(log/default) >= 0.4.29 with crate(log/default) < 0.5.0~)
BuildRequires:  (crate(nix) >= 0.31.3 with crate(nix) < 0.32.0~)
BuildRequires:  (crate(nix/process) >= 0.31.3 with crate(nix/process) < 0.32.0~)
BuildRequires:  (crate(nix/signal) >= 0.31.3 with crate(nix/signal) < 0.32.0~)
BuildRequires:  (crate(serde/default) >= 1.0.228 with crate(serde/default) < 2.0.0~)
BuildRequires:  (crate(serde/derive) >= 1.0.228 with crate(serde/derive) < 2.0.0~)
BuildRequires:  (crate(tokio-util/default) >= 0.7.18 with crate(tokio-util/default) < 0.8.0~)
BuildRequires:  (crate(tokio/default) >= 1.0.0 with crate(tokio/default) < 2.0.0~)
BuildRequires:  (crate(tokio/macros) >= 1.0.0 with crate(tokio/macros) < 2.0.0~)
BuildRequires:  (crate(tokio/process) >= 1.0.0 with crate(tokio/process) < 2.0.0~)
BuildRequires:  (crate(tokio/rt-multi-thread) >= 1.0.0 with crate(tokio/rt-multi-thread) < 2.0.0~)
BuildRequires:  (crate(tokio/sync) >= 1.0.0 with crate(tokio/sync) < 2.0.0~)
BuildRequires:  (crate(toml/default) >= 1.1.2 with crate(toml/default) < 2.0.0~)
BuildRequires:  (crate(zbus) >= 5.0.0 with crate(zbus) < 6.0.0~)
BuildRequires:  (crate(zbus/default) >= 5.0.0 with crate(zbus/default) < 6.0.0~)
BuildRequires:  (crate(zbus/tokio) >= 5.0.0 with crate(zbus/tokio) < 6.0.0~)
BuildRequires:  (crate(zbus_polkit) >= 5.0.0 with crate(zbus_polkit) < 6.0.0~)
BuildRequires:  (crate(zbus_polkit/tokio) >= 5.0.0 with crate(zbus_polkit/tokio) < 6.0.0~)
BuildRequires:  (crate(zvariant/default) >= 5.0.0 with crate(zvariant/default) < 6.0.0~)
BuildRequires:  rust >= 1.56
Requires:  scx-scheds
Obsoletes: scxctl = 0.3.4
Provides: scxctl = %{version}
Conflicts: scx-tools-git

%description
scx_loader: A DBUS Interface for Managing sched_ext Schedulers

%prep
%autosetup -n scx-loader-%{version}
sed -i 's/^lto = "thin"/lto = false/' Cargo.toml
mkdir vendor
tar -xvf %{SOURCE10} -C vendor/
tar -xvf %{SOURCE11} -C vendor/
tar -xvf %{SOURCE12} -C vendor/
tar -xvf %{SOURCE13} -C vendor/
tar -xvf %{SOURCE14} -C vendor/
tar -xvf %{SOURCE15} -C vendor/
tar -xvf %{SOURCE18} -C vendor/
tar -xvf %{SOURCE19} -C vendor/
tar -xvf %{SOURCE20} -C vendor/
tar -xvf %{SOURCE21} -C vendor/
tar -xvf %{SOURCE22} -C vendor/
tar -xvf %{SOURCE23} -C vendor/
tar -xvf %{SOURCE24} -C vendor/
tar -xvf %{SOURCE25} -C vendor/
tar -xvf %{SOURCE26} -C vendor/
sed -i 's/^sysinfo = "0\.39\.5"/sysinfo = "0.38.4"/' crates/scx_loader/Cargo.toml
sed -i \
    -e '/"windows\//d' \
    -e '/"objc2-core-foundation\//d' \
    -e '/"objc2-io-kit/d' \
    -e '/"dep:ntapi"/d' \
    -e '/^\[target.'\''cfg(any(target_os = "macos", target_os = "ios"))'\''.dependencies.objc2-core-foundation\]/,/^$/d' \
    -e '/^\[target.'\''cfg(any(target_os = "macos", target_os = "ios"))'\''.dependencies.objc2-io-kit\]/,/^$/d' \
    -e '/^\[target."cfg(windows)".dependencies.ntapi\]/,/^$/d' \
    -e '/^\[target."cfg(windows)".dependencies.windows\]/,/^$/d' \
    vendor/sysinfo-%{rust_sysinfo_ver}/Cargo.toml
sed -i \
    -e '/"windows-sys\//d' \
    -e '/^\[target."cfg(windows)".dependencies.windows-sys\]/,/^$/d' \
    -e '/^\[target."cfg(windows)".dev-dependencies.windows-sys\]/,/^$/d' \
    vendor/tokio-%{rust_tokio_ver}/Cargo.toml
sed -i \
    -e '/^\[target."cfg(windows)".dependencies.async-recursion\]/,/^$/d' \
    -e '/^\[target."cfg(windows)".dependencies.uds_windows\]/,/^$/d' \
    -e '/^\[target."cfg(windows)".dependencies.windows-sys\]/,/^$/d' \
    vendor/zbus-%{rust_zbus_ver}/Cargo.toml
%cargo_prep
cat >> .cargo/config.toml << EOF

[patch.crates-io]
clap = { path = "vendor/clap-%{rust_clap_ver}" }
clap_builder = { path = "vendor/clap_builder-%{rust_clap_builder_ver}" }
clap_derive = { path = "vendor/clap_derive-%{rust_clap_derive_ver}" }
endi = { path = "vendor/endi-%{rust_endi_ver}" }
ordered-stream = { path = "vendor/ordered-stream-%{rust_ordered_stream_ver}" }
sysinfo = { path = "vendor/sysinfo-%{rust_sysinfo_ver}" }
tokio = { path = "vendor/tokio-%{rust_tokio_ver}" }
tokio-macros = { path = "vendor/tokio-macros-%{rust_tokio_macros_ver}" }
zbus = { path = "vendor/zbus-%{rust_zbus_ver}" }
zbus_macros = { path = "vendor/zbus_macros-%{rust_zbus_macros_ver}" }
zbus_names = { path = "vendor/zbus_names-%{rust_zbus_names_ver}" }
zbus_polkit = { path = "vendor/zbus_polkit-%{rust_zbus_polkit_ver}" }
zvariant = { path = "vendor/zvariant-%{rust_zvariant_ver}" }
zvariant_derive = { path = "vendor/zvariant_derive-%{rust_zvariant_derive_ver}" }
zvariant_utils = { path = "vendor/zvariant_utils-%{rust_zvariant_utils_ver}" }
EOF

%build
%cargo_build -a -- --workspace

%install

# Install all built executables (skip .so and .d files)
find target/rpm \
    -maxdepth 1 -type f -executable ! -name '*.so' ! -name 'xtask' \
    -exec install -Dm755 -t %{buildroot}%{_bindir} {} +

# Install runtime assets via xtask
# (systemd units, D-Bus services, configs, sample files)
./target/rpm/xtask install --destdir %{buildroot}

%files

# Binaries
%{_bindir}/*

# Systemd service
%{_unitdir}/scx_loader.service

# DBus service and configuration
%{_datadir}/dbus-1/system-services/org.scx.Loader.service
%{_datadir}/dbus-1/system.d/org.scx.Loader.conf
%{_datadir}/dbus-1/interfaces/org.scx.Loader.xml

# Polkit authorization policy for scx-loader
%{_datadir}/polkit-1/actions/org.scx.Loader.policy

# Configuration files
%{_datadir}/scx_loader/config.toml
