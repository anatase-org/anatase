Name:           nvidia-persistenced
Version:        595.58.03
Release:        1%{?dist}
Summary:        A daemon to maintain persistent software state in the NVIDIA driver
Epoch:          3
License:        GPLv2+
URL:            http://www.nvidia.com/object/unix.html
ExclusiveArch:  x86_64 aarch64

Source0:        https://download.nvidia.com/XFree86/%{name}/%{name}-%{version}.tar.bz2
Source1:        %{name}.service
Source2:        %{name}-sysusers.conf

BuildRequires:  gcc
BuildRequires:  libtirpc-devel
BuildRequires:  m4
BuildRequires:  systemd-rpm-macros

%{?sysusers_requires_compat}

Requires(post):     systemd
Requires(preun):    systemd
Requires(postun):   systemd
Requires:           libnvidia-cfg%{?_isa} >= %{?epoch:%{epoch}:}%{version}

%description
The %{name} utility is used to enable persistent software state in the NVIDIA
driver. When persistence mode is enabled, the daemon prevents the driver from
releasing device state when the device is not in use. This can improve the
startup time of new clients in this scenario.

%prep
%autosetup
# Remove additional CFLAGS added when enabling DEBUG
sed -i -e '/+= -O0 -g/d' utils.mk

%build
export CFLAGS="%{optflags} -I%{_includedir}/tirpc"
make %{?_smp_mflags} \
    DEBUG=1 \
    LIBS="-ldl -ltirpc" \
    NV_VERBOSE=1 \
    PREFIX=%{_prefix} \
    STRIP_CMD=true

%install
%make_install \
    NV_VERBOSE=1 \
    PREFIX=%{_prefix} \
    STRIP_CMD=true

# Systemd unit files
install -p -m 644 -D %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service

# Systemd user
install -p -D -m 0644 %{SOURCE2} %{buildroot}%{_sysusersdir}/%{name}.conf

%pre
%sysusers_create_compat %{SOURCE2}

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%license COPYING
%{_mandir}/man1/%{name}.1.*
%{_bindir}/%{name}
%{_unitdir}/%{name}.service
%{_sysusersdir}/%{name}.conf

%changelog
* Tue Mar 24 2026 Simone Caronni <negativo17@gmail.com> - 3:595.58.03-1
- Update to 595.58.03.

* Thu Mar 05 2026 Simone Caronni <negativo17@gmail.com> - 3:595.45.04-1
- Update to 595.45.04.

* Thu Dec 18 2025 Simone Caronni <negativo17@gmail.com> - 3:590.48.01-1
- Update to 590.48.01.

* Fri Dec 05 2025 Simone Caronni <negativo17@gmail.com> - 3:590.44.01-1
- Update to 590.44.01.

* Fri Nov 07 2025 Simone Caronni <negativo17@gmail.com> - 3:580.105.08-1
- Update to 580.105.08.

* Wed Oct 01 2025 Simone Caronni <negativo17@gmail.com> - 3:580.95.05-1
- Update to 580.95.05, rework configuration:
  - Run as user nvidia-persistenced, as described in the guide.
  - Allow user to manage the /run/nvidia-persistenced directory.
  - Drop /var/lib/nvidia-persistenced folder.
  - Use sysusers mechanism on EL9+, with compat up to Fedora 41.
  - Fix warning about /var/run paths being used.

* Thu Sep 11 2025 Simone Caronni <negativo17@gmail.com> - 3:580.82.09-1
- Update to 580.82.09.

* Mon Sep 01 2025 Simone Caronni <negativo17@gmail.com> - 3:580.82.07-1
- Update to 580.82.07.

* Thu Aug 14 2025 Simone Caronni <negativo17@gmail.com> - 3:580.76.05-1
- Update to 580.76.05.

* Tue Aug 05 2025 Simone Caronni <negativo17@gmail.com> - 3:580.65.06-1
- Update to 580.65.06.

* Wed Jul 23 2025 Simone Caronni <negativo17@gmail.com> - 3:575.64.05-1
- Update to 575.64.05.

* Tue Jul 01 2025 Simone Caronni <negativo17@gmail.com> - 3:575.64.03-1
- Update to 575.64.03.

* Wed Jun 18 2025 Simone Caronni <negativo17@gmail.com> - 3:575.64-1
- Update to 575.64.

* Thu May 29 2025 Simone Caronni <negativo17@gmail.com> - 3:575.57.08-1
- Update to 575.57.08.

* Tue May 20 2025 Simone Caronni <negativo17@gmail.com> - 3:575.51.02-1
- Update to 575.51.02.

* Tue May 20 2025 Simone Caronni <negativo17@gmail.com> - 3:570.153.02-1
- Update to 570.153.02.

* Tue Apr 22 2025 Simone Caronni <negativo17@gmail.com> - 3:570.144-1
- Update to 570.144.

* Wed Mar 19 2025 Simone Caronni <negativo17@gmail.com> - 3:570.133.07-1
- Update to 570.133.07.

* Mon Mar 10 2025 Simone Caronni <negativo17@gmail.com> - 3:570.124.04-2
- Move nvidia-persistenced binary to _bindir (as per original sources).

* Fri Feb 28 2025 Simone Caronni <negativo17@gmail.com> - 3:570.124.04-1
- Update to 570.124.04.

* Fri Jan 31 2025 Simone Caronni <negativo17@gmail.com> - 3:570.86.16-1
- Update to 570.86.16.

* Mon Jan 27 2025 Simone Caronni <negativo17@gmail.com> - 3:570.86.15-1
- Update to 570.86.15.

* Thu Dec 05 2024 Simone Caronni <negativo17@gmail.com> - 3:565.77-1
- Update to 565.77.

* Wed Oct 23 2024 Simone Caronni <negativo17@gmail.com> - 3:565.57.01-1
- Update to 565.57.01.

* Wed Aug 21 2024 Simone Caronni <negativo17@gmail.com> - 3:560.35.03-1
- Update to 560.35.03.

* Tue Aug 06 2024 Simone Caronni <negativo17@gmail.com> - 3:560.31.02-1
- Update to 560.31.02.

* Mon Aug 05 2024 Simone Caronni <negativo17@gmail.com> - 3:560.28.03-1
- Update to 560.28.03.

* Tue Jul 02 2024 Simone Caronni <negativo17@gmail.com> - 3:555.58.02-1
- Update to 555.58.02.
- Require dynamically loaded library libnvidia-cfg.

* Thu Jun 27 2024 Simone Caronni <negativo17@gmail.com> - 3:555.58-1
- Update to 555.58.

* Thu Jun 06 2024 Simone Caronni <negativo17@gmail.com> - 3:555.52.04-1
- Update to 555.52.04.

* Wed May 22 2024 Simone Caronni <negativo17@gmail.com> - 3:555.42.02-1
- Update to 555.42.02.

* Tue Apr 30 2024 Simone Caronni <negativo17@gmail.com> - 3:550.78-2
- Switch to Nvidia provided tarball.

* Fri Apr 26 2024 Simone Caronni <negativo17@gmail.com> - 3:550.78-1
- Update to 550.78.

* Thu Apr 18 2024 Simone Caronni <negativo17@gmail.com> - 3:550.76-1
- Update to 550.76.

* Sun Mar 24 2024 Simone Caronni <negativo17@gmail.com> - 3:550.67-1
- Update to 550.67.

* Mon Mar 18 2024 Simone Caronni <negativo17@gmail.com> - 3:550.54.14-4
- Clean up build requirements.

* Sat Mar 09 2024 Simone Caronni <negativo17@gmail.com> - 3:550.54.14-3
- Enable aarch64.

* Thu Mar 07 2024 Simone Caronni <negativo17@gmail.com> - 3:550.54.14-2
- Run nvidia-persistenced as root as Nvidia does.

* Sun Mar 03 2024 Simone Caronni <negativo17@gmail.com> - 3:550.54.14-1
- Update to 550.54.14.

* Tue Feb 06 2024 Simone Caronni <negativo17@gmail.com> - 3:550.40.07-1
- Update to 550.40.07.
