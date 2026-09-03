%define _disable_source_fetch 0

# prevent library files from being installed
%global cargo_install_lib 0

# Disable debug package generation
%global debug_package %{nil}

Name:           scx-scheds
Version:        1.1.3
Release:        3%{?dist}
Summary:        Sched_ext Schedulers and Tools

License:        GPL=2.0
URL:            https://github.com/sched-ext/scx
Source0:        %{URL}/archive/refs/tags/v%{version}.tar.gz

# Hotfix PR#3755 for scx_cake. TODO: Remove on dot version bump.
Patch0:         %{URL}/commit/6624f0f178e233b2f733825e5e08549048ca3700.diff
Patch1:         %{URL}/commit/bdbf5eec541fdd48ed825d8e07cebdf5aad10e63.diff
# Hotfix PR#3756 for scx_pandemonium. TODO: Remove on dot version bump.
Patch2:         %{URL}/commit/18dbe236217a907a4f165bb89e8f75a3fda9ab46.diff

%global rust_affinity_ver 0.1.2
%global rust_anpa_ver 0.10.0
%global rust_ascii_ver 1.1.0
%global rust_blazesym_ver 0.2.3
%global rust_buddy_system_allocator_ver 0.13.0
%global rust_cargo_metadata_ver 0.19.2
%global rust_chunked_transfer_ver 1.5.0
%global rust_clap_main_ver 0.2.9
%global rust_combinations_ver 0.1.0
%global rust_convert_case_ver 0.11.0
%global rust_gpoint_ver 0.3.0
%global rust_httpdate_ver 1.0.3
%global rust_libbpf_cargo_ver 0.26.2
%global rust_libbpf_rs_ver 0.26.2
%global rust_libbpf_sys_ver 1.7.0+v1.7.0
%global rust_micromath_ver 2.1.0
%global rust_nvml_wrapper_ver 0.12.1
%global rust_nvml_wrapper_sys_ver 0.9.1
%global rust_perf_event_open_sys_ver 6.0.0
%global rust_perfetto_protos_ver 0.51.1
%global rust_seccomp_ver 0.1.2
%global rust_seccomp_sys_ver 0.1.3
%global rust_sorted_vec_ver 0.8.10
%global rust_sscanf_ver 0.5.0
%global rust_sscanf_macro_ver 0.5.0
%global rust_sysinfo_ver 0.38.4
%global rust_tachyonfx_ver 0.25.0
%global rust_tiny_http_ver 0.12.0
%global rust_vsprintf_ver 2.0.0
%global rust_wrapcenum_derive_ver 0.4.1
Source10:       https://crates.io/api/v1/crates/affinity/%{rust_affinity_ver}/download#/affinity-%{rust_affinity_ver}.tar.gz
Source11:       https://crates.io/api/v1/crates/blazesym/%{rust_blazesym_ver}/download#/blazesym-%{rust_blazesym_ver}.tar.gz
Source12:       https://crates.io/api/v1/crates/buddy_system_allocator/%{rust_buddy_system_allocator_ver}/download#/buddy_system_allocator-%{rust_buddy_system_allocator_ver}.tar.gz
Source13:       https://crates.io/api/v1/crates/clap_main/%{rust_clap_main_ver}/download#/clap_main-%{rust_clap_main_ver}.tar.gz
Source14:       https://crates.io/api/v1/crates/combinations/%{rust_combinations_ver}/download#/combinations-%{rust_combinations_ver}.tar.gz
Source15:       https://crates.io/api/v1/crates/gpoint/%{rust_gpoint_ver}/download#/gpoint-%{rust_gpoint_ver}.tar.gz
Source16:       https://crates.io/api/v1/crates/libbpf-cargo/%{rust_libbpf_cargo_ver}/download#/libbpf-cargo-%{rust_libbpf_cargo_ver}.tar.gz
Source17:       https://crates.io/api/v1/crates/libbpf-rs/%{rust_libbpf_rs_ver}/download#/libbpf-rs-%{rust_libbpf_rs_ver}.tar.gz
Source18:       https://crates.io/api/v1/crates/libbpf-sys/%{rust_libbpf_sys_ver}/download#/libbpf-sys-%{rust_libbpf_sys_ver}.tar.gz
Source19:       https://crates.io/api/v1/crates/nvml-wrapper/%{rust_nvml_wrapper_ver}/download#/nvml-wrapper-%{rust_nvml_wrapper_ver}.tar.gz
Source20:       https://crates.io/api/v1/crates/nvml-wrapper-sys/%{rust_nvml_wrapper_sys_ver}/download#/nvml-wrapper-sys-%{rust_nvml_wrapper_sys_ver}.tar.gz
Source21:       https://crates.io/api/v1/crates/perf-event-open-sys/%{rust_perf_event_open_sys_ver}/download#/perf-event-open-sys-%{rust_perf_event_open_sys_ver}.tar.gz
Source22:       https://crates.io/api/v1/crates/perfetto_protos/%{rust_perfetto_protos_ver}/download#/perfetto_protos-%{rust_perfetto_protos_ver}.tar.gz
Source23:       https://crates.io/api/v1/crates/seccomp/%{rust_seccomp_ver}/download#/seccomp-%{rust_seccomp_ver}.tar.gz
Source24:       https://crates.io/api/v1/crates/sorted-vec/%{rust_sorted_vec_ver}/download#/sorted-vec-%{rust_sorted_vec_ver}.tar.gz
Source25:       https://crates.io/api/v1/crates/sscanf/%{rust_sscanf_ver}/download#/sscanf-%{rust_sscanf_ver}.tar.gz
Source26:       https://crates.io/api/v1/crates/sysinfo/%{rust_sysinfo_ver}/download#/sysinfo-%{rust_sysinfo_ver}.tar.gz
Source27:       https://crates.io/api/v1/crates/tachyonfx/%{rust_tachyonfx_ver}/download#/tachyonfx-%{rust_tachyonfx_ver}.tar.gz
Source28:       https://crates.io/api/v1/crates/vsprintf/%{rust_vsprintf_ver}/download#/vsprintf-%{rust_vsprintf_ver}.tar.gz
Source29:       https://crates.io/api/v1/crates/cargo_metadata/%{rust_cargo_metadata_ver}/download#/cargo_metadata-%{rust_cargo_metadata_ver}.tar.gz
Source30:       https://crates.io/api/v1/crates/wrapcenum-derive/%{rust_wrapcenum_derive_ver}/download#/wrapcenum-derive-%{rust_wrapcenum_derive_ver}.tar.gz
Source31:       https://crates.io/api/v1/crates/sscanf_macro/%{rust_sscanf_macro_ver}/download#/sscanf_macro-%{rust_sscanf_macro_ver}.tar.gz
Source32:       https://crates.io/api/v1/crates/seccomp-sys/%{rust_seccomp_sys_ver}/download#/seccomp-sys-%{rust_seccomp_sys_ver}.tar.gz
Source33:       https://crates.io/api/v1/crates/anpa/%{rust_anpa_ver}/download#/anpa-%{rust_anpa_ver}.tar.gz
Source34:       https://crates.io/api/v1/crates/micromath/%{rust_micromath_ver}/download#/micromath-%{rust_micromath_ver}.tar.gz
Source35:       https://crates.io/api/v1/crates/convert_case/%{rust_convert_case_ver}/download#/convert_case-%{rust_convert_case_ver}.tar.gz
Source36:       https://crates.io/api/v1/crates/ascii/%{rust_ascii_ver}/download#/ascii-%{rust_ascii_ver}.tar.gz
Source37:       https://crates.io/api/v1/crates/chunked_transfer/%{rust_chunked_transfer_ver}/download#/chunked_transfer-%{rust_chunked_transfer_ver}.tar.gz
Source38:       https://crates.io/api/v1/crates/httpdate/%{rust_httpdate_ver}/download#/httpdate-%{rust_httpdate_ver}.tar.gz
Source39:       https://crates.io/api/v1/crates/tiny_http/%{rust_tiny_http_ver}/download#/tiny_http-%{rust_tiny_http_ver}.tar.gz

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
BuildRequires:  elfutils-libelf
BuildRequires:  elfutils-libelf-devel
BuildRequires:  zlib
BuildRequires:  jq
BuildRequires:  jq-devel
BuildRequires:  systemd
BuildRequires:  bpftool
BuildRequires:  protobuf-compiler
BuildRequires:  libseccomp-devel
BuildRequires: openssl-devel

BuildRequires:  (crate(anyhow/default) >= 1.0.0 with crate(anyhow/default) < 2.0.0~)
BuildRequires:  (crate(arboard/default) >= 3.0.0 with crate(arboard/default) < 4.0.0~)
BuildRequires:  (crate(bitvec/default) >= 1.0.0 with crate(bitvec/default) < 2.0.0~)
BuildRequires:  (crate(bitvec/serde) >= 1.0.0 with crate(bitvec/serde) < 2.0.0~)
BuildRequires:  (crate(bon/default) >= 3.9.0 with crate(bon/default) < 4.0.0~)
BuildRequires:  (crate(cargo-platform/default) >= 0.1.2 with crate(cargo-platform/default) < 0.2.0~)
BuildRequires:  (crate(cargo_metadata/default) >= 0.23.0 with crate(cargo_metadata/default) < 0.24.0~)
BuildRequires:  (crate(cc/default) >= 1.0.0 with crate(cc/default) < 2.0.0~)
BuildRequires:  (crate(cgroupfs/default) >= 0.9.0 with crate(cgroupfs/default) < 0.10.0~)
BuildRequires:  (crate(chrono/default) >= 0.4.0 with crate(chrono/default) < 0.5.0~)
BuildRequires:  (crate(clap-num/default) >= 1.0.0 with crate(clap-num/default) < 2.0.0~)
BuildRequires:  (crate(clap/cargo) >= 4.0.0 with crate(clap/cargo) < 5.0.0~)
BuildRequires:  (crate(clap/default) >= 4.0.0 with crate(clap/default) < 5.0.0~)
BuildRequires:  (crate(clap/derive) >= 4.0.0 with crate(clap/derive) < 5.0.0~)
BuildRequires:  (crate(clap/env) >= 4.0.0 with crate(clap/env) < 5.0.0~)
BuildRequires:  (crate(clap/string) >= 4.0.0 with crate(clap/string) < 5.0.0~)
BuildRequires:  (crate(clap/unicode) >= 4.0.0 with crate(clap/unicode) < 5.0.0~)
BuildRequires:  (crate(clap/unstable-styles) >= 4.0.0 with crate(clap/unstable-styles) < 5.0.0~)
BuildRequires:  (crate(clap/wrap_help) >= 4.0.0 with crate(clap/wrap_help) < 5.0.0~)
BuildRequires:  (crate(clap_complete/default) >= 4.0.0 with crate(clap_complete/default) < 5.0.0~)
BuildRequires:  (crate(core_affinity/default) >= 0.8.0 with crate(core_affinity/default) < 0.9.0~)
BuildRequires:  (crate(cpp_demangle/default) >= 0.5.0 with crate(cpp_demangle/default) < 0.6.0~)
BuildRequires:  (crate(crossbeam-utils/default) >= 0.8.0 with crate(crossbeam-utils/default) < 0.9.0~)
BuildRequires:  (crate(crossbeam/default) >= 0.8.0 with crate(crossbeam/default) < 0.9.0~)
BuildRequires:  (crate(crossterm/default) >= 0.29.0 with crate(crossterm/default) < 0.30.0~)
BuildRequires:  (crate(crossterm/event-stream) >= 0.29.0 with crate(crossterm/event-stream) < 0.30.0~)
BuildRequires:  (crate(crossterm/serde) >= 0.29.0 with crate(crossterm/serde) < 0.30.0~)
BuildRequires:  (crate(csv/default) >= 1.0.0 with crate(csv/default) < 2.0.0~)
BuildRequires:  (crate(ctrlc/default) >= 3.0.0 with crate(ctrlc/default) < 4.0.0~)
BuildRequires:  (crate(ctrlc/termination) >= 3.0.0 with crate(ctrlc/termination) < 4.0.0~)
BuildRequires:  (crate(env_logger/default) >= 0.11.0 with crate(env_logger/default) < 0.12.0~)
BuildRequires:  (crate(fastrand/default) >= 2.0.0 with crate(fastrand/default) < 3.0.0~)
BuildRequires:  (crate(fb_procfs/default) >= 0.9.0 with crate(fb_procfs/default) < 0.10.0~)
BuildRequires:  (crate(flate2/default) >= 1.0.0 with crate(flate2/default) < 2.0.0~)
BuildRequires:  (crate(futures/default) >= 0.3.0 with crate(futures/default) < 0.4.0~)
BuildRequires:  (crate(gimli/default) >= 0.32.0 with crate(gimli/default) < 0.33.0~)
BuildRequires:  (crate(glob/default) >= 0.3.0 with crate(glob/default) < 0.4.0~)
BuildRequires:  (crate(hashbrown/default) >= 0.16.0 with crate(hashbrown/default) < 0.17.0~)
BuildRequires:  (crate(hex/default) >= 0.4.0 with crate(hex/default) < 0.5.0~)
BuildRequires:  (crate(include_dir/default) >= 0.7.0 with crate(include_dir/default) < 0.8.0~)
BuildRequires:  (crate(indoc/default) >= 2.0.0 with crate(indoc/default) < 3.0.0~)
BuildRequires:  (crate(inotify/default) >= 0.11.0 with crate(inotify/default) < 0.12.0~)
BuildRequires:  (crate(itertools/default) >= 0.14.0 with crate(itertools/default) < 0.15.0~)
BuildRequires:  (crate(lazy_static/default) >= 1.0.0 with crate(lazy_static/default) < 2.0.0~)
BuildRequires:  (crate(libc/default) >= 0.2.0 with crate(libc/default) < 0.3.0~)
BuildRequires:  (crate(log-panics/default) >= 2.0.0 with crate(log-panics/default) < 3.0.0~)
BuildRequires:  (crate(log-panics/with-backtrace) >= 2.0.0 with crate(log-panics/with-backtrace) < 3.0.0~)
BuildRequires:  (crate(log/default) >= 0.4.0 with crate(log/default) < 0.5.0~)
BuildRequires:  (crate(maplit/default) >= 1.0.0 with crate(maplit/default) < 2.0.0~)
BuildRequires:  (crate(memmap2/default) >= 0.9.0 with crate(memmap2/default) < 0.10.0~)
BuildRequires:  (crate(miniz_oxide/simd) >= 0.9.0 with crate(miniz_oxide/simd) < 0.10.0~)
BuildRequires:  (crate(miniz_oxide/with-alloc) >= 0.9.0 with crate(miniz_oxide/with-alloc) < 0.10.0~)
BuildRequires:  (crate(nix/default) >= 0.31.0 with crate(nix/default) < 0.32.0~)
BuildRequires:  (crate(nix/event) >= 0.31.0 with crate(nix/event) < 0.32.0~)
BuildRequires:  (crate(nix/poll) >= 0.31.0 with crate(nix/poll) < 0.32.0~)
BuildRequires:  (crate(nix/process) >= 0.31.0 with crate(nix/process) < 0.32.0~)
BuildRequires:  (crate(nix/resource) >= 0.31.0 with crate(nix/resource) < 0.32.0~)
BuildRequires:  (crate(nix/sched) >= 0.31.0 with crate(nix/sched) < 0.32.0~)
BuildRequires:  (crate(nix/signal) >= 0.31.0 with crate(nix/signal) < 0.32.0~)
BuildRequires:  (crate(nix/time) >= 0.31.0 with crate(nix/time) < 0.32.0~)
BuildRequires:  (crate(nix/user) >= 0.31.0 with crate(nix/user) < 0.32.0~)
BuildRequires:  (crate(num-format/default) >= 0.4.0 with crate(num-format/default) < 0.5.0~)
BuildRequires:  (crate(num-format/with-serde) >= 0.4.0 with crate(num-format/with-serde) < 0.5.0~)
BuildRequires:  (crate(num-format/with-system-locale) >= 0.4.0 with crate(num-format/with-system-locale) < 0.5.0~)
BuildRequires:  (crate(num/default) >= 0.4.0 with crate(num/default) < 0.5.0~)
BuildRequires:  (crate(num_cpus/default) >= 1.0.0 with crate(num_cpus/default) < 2.0.0~)
BuildRequires:  (crate(object/default) >= 0.38.0 with crate(object/default) < 0.39.0~)
BuildRequires:  (crate(once_cell/default) >= 1.0.0 with crate(once_cell/default) < 2.0.0~)
BuildRequires:  (crate(ordered-float/default) >= 5.0.0 with crate(ordered-float/default) < 6.0.0~)
BuildRequires:  (crate(paste/default) >= 1.0.0 with crate(paste/default) < 2.0.0~)
BuildRequires:  (crate(pkg-config/default) >= 0.3.0 with crate(pkg-config/default) < 0.4.0~)
BuildRequires:  (crate(plain/default) >= 0.2.0 with crate(plain/default) < 0.3.0~)
BuildRequires:  (crate(proc-macro2/default) >= 1.0.0 with crate(proc-macro2/default) < 2.0.0~)
BuildRequires:  (crate(procfs/default) >= 0.18.0 with crate(procfs/default) < 0.19.0~)
BuildRequires:  (crate(protobuf-codegen/default) >= 3.7.1 with crate(protobuf-codegen/default) < 4.0.0~)
BuildRequires:  (crate(protobuf/default) >= 3.0.0 with crate(protobuf/default) < 4.0.0~)
BuildRequires:  (crate(quanta/default) >= 0.12.0 with crate(quanta/default) < 0.13.0~)
BuildRequires:  (crate(quote/default) >= 1.0.0 with crate(quote/default) < 2.0.0~)
BuildRequires:  (crate(rand/default) >= 0.10.0 with crate(rand/default) < 0.11.0~)
BuildRequires:  (crate(ratatui/default) >= 0.30.0 with crate(ratatui/default) < 0.31.0~)
BuildRequires:  (crate(ratatui/macros) >= 0.30.0 with crate(ratatui/macros) < 0.31.0~)
BuildRequires:  (crate(ratatui/serde) >= 0.30.0 with crate(ratatui/serde) < 0.31.0~)
BuildRequires:  (crate(rayon/default) >= 1.0.0 with crate(rayon/default) < 2.0.0~)
BuildRequires:  (crate(regex/default) >= 1.0.0 with crate(regex/default) < 2.0.0~)
BuildRequires:  (crate(rlimit/default) >= 0.11.0 with crate(rlimit/default) < 0.12.0~)
BuildRequires:  (crate(rustc-demangle/default) >= 0.1.0 with crate(rustc-demangle/default) < 0.2.0~)
BuildRequires:  (crate(ruzstd/default) >= 0.8.0 with crate(ruzstd/default) < 0.9.0~)
BuildRequires:  (crate(serde/default) >= 1.0.0 with crate(serde/default) < 2.0.0~)
BuildRequires:  (crate(serde/derive) >= 1.0.0 with crate(serde/derive) < 2.0.0~)
BuildRequires:  (crate(serde_json/default) >= 1.0.0 with crate(serde_json/default) < 2.0.0~)
BuildRequires:  (crate(signal-hook/default) >= 0.4.0 with crate(signal-hook/default) < 0.5.0~)
BuildRequires:  (crate(simplelog/default) >= 0.12.0 with crate(simplelog/default) < 0.13.0~)
BuildRequires:  (crate(smartstring/default) >= 1.0.0 with crate(smartstring/default) < 2.0.0~)
BuildRequires:  (crate(smartstring/serde) >= 1.0.0 with crate(smartstring/serde) < 2.0.0~)
BuildRequires:  (crate(static_assertions/default) >= 1.0.0 with crate(static_assertions/default) < 2.0.0~)
BuildRequires:  (crate(syn/default) >= 2.0.0 with crate(syn/default) < 3.0.0~)
BuildRequires:  (crate(syn/extra-traits) >= 2.0.0 with crate(syn/extra-traits) < 3.0.0~)
BuildRequires:  (crate(syn/full) >= 2.0.0 with crate(syn/full) < 3.0.0~)
BuildRequires:  (crate(tar/default) >= 0.4.0 with crate(tar/default) < 0.5.0~)
BuildRequires:  (crate(tempfile/default) >= 3.0.0 with crate(tempfile/default) < 4.0.0~)
BuildRequires:  (crate(tokio-util/default) >= 0.7.0 with crate(tokio-util/default) < 0.8.0~)
BuildRequires:  (crate(tokio/default) >= 1.0.0 with crate(tokio/default) < 2.0.0~)
BuildRequires:  (crate(tokio/full) >= 1.0.0 with crate(tokio/full) < 2.0.0~)
BuildRequires:  (crate(toml/default) >= 1.0.0 with crate(toml/default) < 2.0.0~)
BuildRequires:  (crate(tracing-subscriber/default) >= 0.3.0 with crate(tracing-subscriber/default) < 0.4.0~)
BuildRequires:  (crate(tracing-subscriber/env-filter) >= 0.3.0 with crate(tracing-subscriber/env-filter) < 0.4.0~)
BuildRequires:  (crate(tracing-subscriber/fmt) >= 0.3.0 with crate(tracing-subscriber/fmt) < 0.4.0~)
BuildRequires:  (crate(tracing-subscriber/parking_lot) >= 0.3.0 with crate(tracing-subscriber/parking_lot) < 0.4.0~)
BuildRequires:  (crate(tracing-subscriber/tracing-log) >= 0.3.0 with crate(tracing-subscriber/tracing-log) < 0.4.0~)
BuildRequires:  (crate(tracing/default) >= 0.1.0 with crate(tracing/default) < 0.2.0~)
BuildRequires:  (crate(version-compare/default) >= 0.2.0 with crate(version-compare/default) < 0.3.0~)
BuildRequires:  (crate(walkdir/default) >= 2.0.0 with crate(walkdir/default) < 3.0.0~)
BuildRequires:  (crate(xdg/default) >= 3.0.0 with crate(xdg/default) < 4.0.0~)
BuildRequires:  (crate(zbus/default) >= 5.0.0 with crate(zbus/default) < 6.0.0~)
BuildRequires:  crate(bindgen/default) >= 0.69.0
BuildRequires:  rust >= 1.56

Requires:  elfutils-libelf
Requires:  libseccomp
Requires:  protobuf
Requires:  zlib
Requires:  jq
Requires:  scx-tools
Conflicts: scx-scheds-git
Conflicts: scx_layered
Conflicts: scx_rustland
Conflicts: scx_rusty
Conflicts: rust-scx_utils-devel
Provides: scx_layered
Provides: scx_rustland
Provides: scx_rusty
Provides: rust-scx_utils-devel

%description
sched_ext is a Linux kernel feature which enables implementing kernel thread schedulers in BPF and dynamically loading them. This repository contains various scheduler implementations and support utilities.

%prep
%autosetup -n scx-%{version} -p1
sed -i 's/^lto = "thin"/lto = false/' Cargo.toml
mkdir vendor
tar -xvf %{SOURCE10} -C vendor/
tar -xvf %{SOURCE11} -C vendor/
tar -xvf %{SOURCE12} -C vendor/
tar -xvf %{SOURCE13} -C vendor/
tar -xvf %{SOURCE14} -C vendor/
tar -xvf %{SOURCE15} -C vendor/
tar -xvf %{SOURCE16} -C vendor/
tar -xvf %{SOURCE17} -C vendor/
tar -xvf %{SOURCE18} -C vendor/
tar -xvf %{SOURCE19} -C vendor/
tar -xvf %{SOURCE20} -C vendor/
tar -xvf %{SOURCE21} -C vendor/
tar -xvf %{SOURCE22} -C vendor/
tar -xvf %{SOURCE23} -C vendor/
tar -xvf %{SOURCE24} -C vendor/
tar -xvf %{SOURCE25} -C vendor/
tar -xvf %{SOURCE26} -C vendor/
tar -xvf %{SOURCE27} -C vendor/
tar -xvf %{SOURCE28} -C vendor/
tar -xvf %{SOURCE29} -C vendor/
tar -xvf %{SOURCE30} -C vendor/
tar -xvf %{SOURCE31} -C vendor/
tar -xvf %{SOURCE32} -C vendor/
tar -xvf %{SOURCE33} -C vendor/
tar -xvf %{SOURCE34} -C vendor/
tar -xvf %{SOURCE35} -C vendor/
tar -xvf %{SOURCE36} -C vendor/
tar -xvf %{SOURCE37} -C vendor/
tar -xvf %{SOURCE38} -C vendor/
tar -xvf %{SOURCE39} -C vendor/
sed -i \
    -e '/^\[build-dependencies.protoc-bin-vendored\]/,/^$/d' \
    vendor/perfetto_protos-%{rust_perfetto_protos_ver}/Cargo.toml
sed -i 's/let protoc = &protoc_bin_vendored::protoc_bin_path().unwrap();/let protoc = std::path::Path::new("protoc");/' vendor/perfetto_protos-%{rust_perfetto_protos_ver}/build.rs
sed -i \
    -e '/^    let files = deps$/,+3c\    let files = deps\
        .lines()\
        .map(|line| line.trim().trim_end_matches('\''\\\\'\''))\
        .flat_map(|line| line.split_whitespace());' \
    vendor/perfetto_protos-%{rust_perfetto_protos_ver}/build.rs
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
%cargo_prep
cat >> .cargo/config.toml << EOF

[patch.crates-io]
affinity = { path = "vendor/affinity-%{rust_affinity_ver}" }
anpa = { path = "vendor/anpa-%{rust_anpa_ver}" }
ascii = { path = "vendor/ascii-%{rust_ascii_ver}" }
blazesym = { path = "vendor/blazesym-%{rust_blazesym_ver}" }
buddy_system_allocator = { path = "vendor/buddy_system_allocator-%{rust_buddy_system_allocator_ver}" }
cargo_metadata = { path = "vendor/cargo_metadata-%{rust_cargo_metadata_ver}" }
chunked_transfer = { path = "vendor/chunked_transfer-%{rust_chunked_transfer_ver}" }
clap_main = { path = "vendor/clap_main-%{rust_clap_main_ver}" }
combinations = { path = "vendor/combinations-%{rust_combinations_ver}" }
convert_case = { path = "vendor/convert_case-%{rust_convert_case_ver}" }
gpoint = { path = "vendor/gpoint-%{rust_gpoint_ver}" }
httpdate = { path = "vendor/httpdate-%{rust_httpdate_ver}" }
libbpf-cargo = { path = "vendor/libbpf-cargo-%{rust_libbpf_cargo_ver}" }
libbpf-rs = { path = "vendor/libbpf-rs-%{rust_libbpf_rs_ver}" }
libbpf-sys = { path = "vendor/libbpf-sys-%{rust_libbpf_sys_ver}" }
micromath = { path = "vendor/micromath-%{rust_micromath_ver}" }
nvml-wrapper = { path = "vendor/nvml-wrapper-%{rust_nvml_wrapper_ver}" }
nvml-wrapper-sys = { path = "vendor/nvml-wrapper-sys-%{rust_nvml_wrapper_sys_ver}" }
perf-event-open-sys = { path = "vendor/perf-event-open-sys-%{rust_perf_event_open_sys_ver}" }
perfetto_protos = { path = "vendor/perfetto_protos-%{rust_perfetto_protos_ver}" }
seccomp = { path = "vendor/seccomp-%{rust_seccomp_ver}" }
seccomp-sys = { path = "vendor/seccomp-sys-%{rust_seccomp_sys_ver}" }
sorted-vec = { path = "vendor/sorted-vec-%{rust_sorted_vec_ver}" }
sscanf = { path = "vendor/sscanf-%{rust_sscanf_ver}" }
sscanf_macro = { path = "vendor/sscanf_macro-%{rust_sscanf_macro_ver}" }
sysinfo = { path = "vendor/sysinfo-%{rust_sysinfo_ver}" }
tachyonfx = { path = "vendor/tachyonfx-%{rust_tachyonfx_ver}" }
tiny_http = { path = "vendor/tiny_http-%{rust_tiny_http_ver}" }
vsprintf = { path = "vendor/vsprintf-%{rust_vsprintf_ver}" }
wrapcenum-derive = { path = "vendor/wrapcenum-derive-%{rust_wrapcenum_derive_ver}" }
EOF

%build
%cargo_build -a -- --frozen --workspace --exclude scx_rlfifo --exclude scx_mitosis --exclude xtask --exclude scx_characterize --exclude vmlinux_docify --exclude scx_arena_selftests --exclude scx_forge_agent

%install

# Install all built executables (skip .so and .d files)
find target/rpm \
    -maxdepth 1 -type f -executable ! -name '*.so' \
    -exec install -Dm755 -t %{buildroot}%{_bindir} {} +

%files

# Binaries
%{_bindir}/*
