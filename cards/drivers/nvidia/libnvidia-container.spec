%global debug_package %{nil}
# Keep in sync with nvidia-modprobe/nvidia-modprobe.spec.
%global modprobe_version 615.78.08

Name:           libnvidia-container
Version:        1.20.1
Release:        1%{?dist}
Summary:        NVIDIA container runtime library
License:        Apache-2.0 AND GPL-2.0-only AND GPL-3.0-or-later AND LGPL-3.0-or-later AND MIT AND BSD-3-Clause
URL:            https://github.com/NVIDIA/libnvidia-container
Source0:        %{url}/archive/refs/tags/v%{version}.tar.gz
Source1:        https://download.nvidia.com/XFree86/nvidia-modprobe/nvidia-modprobe-%{modprobe_version}.tar.bz2
ExclusiveArch:  x86_64 aarch64

BuildRequires:  gcc
BuildRequires:  golang
BuildRequires:  make
BuildRequires:  patch
BuildRequires:  pkgconfig(libcap)
BuildRequires:  pkgconfig(libelf)
BuildRequires:  pkgconfig(libseccomp)
BuildRequires:  pkgconfig(libtirpc)
BuildRequires:  rpcgen
BuildRequires:  which

%description
Library and command-line tools for configuring containers with NVIDIA GPUs.

%package -n libnvidia-container1
Summary:        NVIDIA container runtime libraries

%description -n libnvidia-container1
Runtime libraries for configuring containers with NVIDIA GPUs.

%package tools
Summary:        NVIDIA container runtime command-line tools
Requires:       libnvidia-container1%{?_isa} = %{version}-%{release}

%description tools
The nvidia-container-cli utility for inspecting and configuring NVIDIA GPUs
inside containers.

%prep
%autosetup
mkdir -p deps/src
tar -xf %{SOURCE1} -C deps/src
patch -d deps/src/nvidia-modprobe-%{modprobe_version} -p1 < mk/nvidia-modprobe.patch
cp deps/src/nvidia-modprobe-%{modprobe_version}/COPYING MODPROBE-COPYING
touch deps/src/nvidia-modprobe-%{modprobe_version}/.download_stamp
sed -i 's/^VERSION        := .*/VERSION        := %{modprobe_version}/' mk/nvidia-modprobe.mk

# Use Fedora's shared libtirpc instead of downloading and building a static copy.
sed -i \
    -e 's|-isystem $(DEPS_DIR)$(includedir)/tirpc|$(shell pkg-config --cflags libtirpc)|' \
    -e 's|-l:libtirpc.a|-ltirpc|' \
    -e '/$(MAKE) -f $(MAKE_DIR)\/libtirpc.mk DESTDIR=$(DEPS_DIR) install/d' \
    -e '/^BIN_LDFLAGS /s/ -Wl,-rpath=.*$//' \
    Makefile

%build
export GOFLAGS="-mod=vendor -buildvcs=false -trimpath"
export GOPROXY=off
export GOTOOLCHAIN=local
export CFLAGS="%{optflags}"
export LDFLAGS="%{?build_ldflags}"
%make_build shared tools \
    LIB_VERSION=%{version} REVISION=v%{version} \
    prefix=%{_prefix} libdir=%{_libdir} \
    WITH_LIBELF=yes WITH_TIRPC=yes WITH_SECCOMP=yes

%install
install -Dm0755 libnvidia-container.so.%{version} \
    %{buildroot}%{_libdir}/libnvidia-container.so.%{version}
install -m0755 deps%{_libdir}/libnvidia-container-go.so.%{version} \
    %{buildroot}%{_libdir}/libnvidia-container-go.so.%{version}
ln -s libnvidia-container.so.%{version} %{buildroot}%{_libdir}/libnvidia-container.so.1
ln -s libnvidia-container-go.so.%{version} %{buildroot}%{_libdir}/libnvidia-container-go.so.1
install -Dm0755 nvidia-container-cli %{buildroot}%{_bindir}/nvidia-container-cli

%files -n libnvidia-container1
%license LICENSE NOTICE COPYING COPYING.LESSER
%license MODPROBE-COPYING
%{_libdir}/libnvidia-container.so.1
%{_libdir}/libnvidia-container.so.%{version}
%{_libdir}/libnvidia-container-go.so.1
%{_libdir}/libnvidia-container-go.so.%{version}

%files tools
%license LICENSE NOTICE COPYING COPYING.LESSER
%{_bindir}/nvidia-container-cli
