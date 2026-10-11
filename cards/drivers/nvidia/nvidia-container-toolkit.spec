%global debug_package %{nil}

Name:           nvidia-container-toolkit
Version:        1.20.1
Release:        1%{?dist}
Summary:        NVIDIA GPU support for containers
License:        Apache-2.0
URL:            https://github.com/NVIDIA/nvidia-container-toolkit
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
ExclusiveArch:  x86_64 aarch64

BuildRequires:  gcc
BuildRequires:  golang >= 1.26.0
BuildRequires:  make
BuildRequires:  systemd-rpm-macros
Requires:       %{name}-base%{?_isa} = %{version}-%{release}
Requires:       libnvidia-container-tools%{?_isa} >= %{version}
Requires:       libnvidia-container-tools < 2.0.0
Provides:       nvidia-container-runtime-hook = %{version}-%{release}

%description
Runtime hooks for running containers with NVIDIA GPUs.

%package base
Summary:        NVIDIA container runtime and CDI tools
Provides:       nvidia-container-runtime = %{version}-%{release}
%{?systemd_requires}

%description base
The NVIDIA container runtime, toolkit CLI, and CDI hooks and refresh services.

%prep
%autosetup

%build
export GOFLAGS="-mod=vendor -buildvcs=false -trimpath"
export GOPROXY=off
export GOTOOLCHAIN=local
%make_build binaries PREFIX="%{_builddir}/%{buildsubdir}/bin" \
    VERSION=%{version} GIT_COMMIT=v%{version}

%install
install -dm0755 %{buildroot}%{_bindir}
for binary in nvidia-ctk nvidia-cdi-hook nvidia-container-runtime \
    nvidia-container-runtime.cdi nvidia-container-runtime.legacy \
    nvidia-container-runtime-hook; do
    install -m0755 bin/$binary %{buildroot}%{_bindir}/$binary
done
ln -s nvidia-container-runtime-hook %{buildroot}%{_bindir}/nvidia-container-toolkit

install -dm0755 %{buildroot}%{_sysconfdir}/nvidia-container-runtime
bin/nvidia-ctk --quiet config \
    --config-file=%{buildroot}%{_sysconfdir}/nvidia-container-runtime/config.toml \
    --in-place
install -Dm0644 deployments/systemd/nvidia-cdi-refresh.env \
    %{buildroot}%{_sysconfdir}/nvidia-container-toolkit/nvidia-cdi-refresh.env
install -Dm0644 deployments/systemd/nvidia-cdi-refresh.service \
    %{buildroot}%{_unitdir}/nvidia-cdi-refresh.service
install -Dm0644 deployments/systemd/nvidia-cdi-refresh.path \
    %{buildroot}%{_unitdir}/nvidia-cdi-refresh.path

%post base
%systemd_post nvidia-cdi-refresh.service nvidia-cdi-refresh.path

%preun base
%systemd_preun nvidia-cdi-refresh.service nvidia-cdi-refresh.path

%postun base
%systemd_postun_with_restart nvidia-cdi-refresh.service nvidia-cdi-refresh.path

%files
%license LICENSE THIRD_PARTY_NOTICES.md
%{_bindir}/nvidia-container-runtime-hook
%{_bindir}/nvidia-container-toolkit

%files base
%license LICENSE THIRD_PARTY_NOTICES.md
%{_bindir}/nvidia-ctk
%{_bindir}/nvidia-cdi-hook
%{_bindir}/nvidia-container-runtime
%{_bindir}/nvidia-container-runtime.cdi
%{_bindir}/nvidia-container-runtime.legacy
%dir %{_sysconfdir}/nvidia-container-runtime
%config(noreplace) %{_sysconfdir}/nvidia-container-runtime/config.toml
%dir %{_sysconfdir}/nvidia-container-toolkit
%config(noreplace) %{_sysconfdir}/nvidia-container-toolkit/nvidia-cdi-refresh.env
%{_unitdir}/nvidia-cdi-refresh.service
%{_unitdir}/nvidia-cdi-refresh.path
