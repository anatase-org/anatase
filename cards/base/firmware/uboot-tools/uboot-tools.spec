#global candidate rc0
%if 0%{?rhel}
%bcond_with toolsonly
%else
%bcond_without toolsonly
%endif

# Set it to "opensbi" (stable) or "opensbi-unstable" (unstable, git)
%global opensbi opensbi

Name:     uboot-tools
Version:  2026.10
Release:  1%{?candidate:.%{candidate}}%{?dist}
Epoch:    1
Summary:  U-Boot utilities
# Automatically converted from old format: GPLv2+ BSD LGPL-2.1+ LGPL-2.0+ - review is highly recommended.
License:  GPL-2.0-or-later AND LicenseRef-Callaway-BSD AND LGPL-2.1-or-later AND LGPL-2.0-or-later
URL:      https://u-boot-project.org/
ExcludeArch: s390x
Source0:  https://git.u-boot-project.org/u-boot/u-boot/-/archive/v%{version}%{?candidate:-%{candidate}}/u-boot-v%{version}%{?candidate:-%{candidate}}.tar.bz2
Source1:  aarch64-boards
Source2:  riscv64-boards
Source3:  x86_64-boards

# Fedora patches to enable/disable features
Patch1:   disable-VBE-by-default.patch
Patch2:   enable-bootmenu-by-default.patch
# This is now legacy, most devices use bootflow, we keep this for the laggards
Patch3:   uefi-distro-load-FDT-from-any-partition-on-boot-device.patch
# Identify VFAT partitions as ESP, allows EFI setvar on our images
Patch4:   uefi-Add-all-options-for-EFI-System-Partitions.patch
# New function to find fdt for loading from disk
Patch5:   uefi-initial-find_fdt_location-for-finding-the-DT-on-disk.patch
# Enable UEFI SetVariable for devices without backed storage
Patch6:   uefi-enable-SetVariableRT-with-volotile-storage.patch
# Enable UEFI HTTPS boot for all Fedora firmware
Patch7:   uefi-enable-https-boot-by-default.patch

# Device improvments
# USB-PD improvements
Patch10:  USB-PD-TCPM-improvements.patch
# Rockchips improvements
Patch11:  rockchip-Enable-preboot-start-for-pci-usb.patch
Patch13:  rockchip-rk356x-Stop-overriding-sdhci-mmc-aliases.patch
# Jetson fixes
Patch14:  p3450-fix-board.patch
Patch15:  JetsonTX2-Fix-upstream-device-tree-naming.patch
# Fix AllWinner
Patch16:  Allwinner-fix-booting-on-a-number-of-devices.patch
# RPi
Patch20:  Fix-NVMe-not-only-on-Raspberry-Pi-5.patch
Patch21:  raspberrypi-Add-quirk-for-RPi5-2Gb-rev-1.0.patch
Patch22:  rpi-copy-chosen-bootloader-partition-and-set-boot_partition.patch

# Our changes
Patch40:  overrides.patch

BuildRequires:  bc
BuildRequires:  bison
BuildRequires:  dtc
BuildRequires:  flex
BuildRequires:  gcc
BuildRequires:  gnutls-devel
BuildRequires:  libuuid-devel
BuildRequires:  make
BuildRequires:  ncurses-devel
%if 0%{?fedora} > 44
BuildRequires:  openssl3-devel
BuildRequires:  openssl3-devel-engine
%else
BuildRequires:  openssl-devel
BuildRequires:  openssl-devel-engine
%endif
BuildRequires:  perl-interpreter
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-libfdt
BuildRequires:  SDL2-devel
BuildRequires:  swig
%if %{with toolsonly}
%ifarch aarch64
BuildRequires:  python3-pyelftools
BuildRequires:  xxd
%endif
%ifarch riscv64
BuildRequires:  %{opensbi}
%endif
%endif
Requires:       dtc

%description
This package contains a few U-Boot utilities - mkimage for creating boot images
and fw_printenv/fw_setenv for manipulating the boot environment variables.

%if %{with toolsonly}
%ifarch aarch64
%package     -n uboot-images-armv8
Summary:     U-Boot firmware images for aarch64 boards
BuildArch:   noarch

%description -n uboot-images-armv8
U-Boot firmware binaries for aarch64 boards
%endif

%ifarch riscv64
%package     -n uboot-images-riscv64
Summary:     U-Boot firmware images for riscv64 boards
BuildArch:   noarch

%description -n uboot-images-riscv64
U-Boot firmware binaries for riscv64 boards
%endif

%ifarch x86_64
%package     -n uboot-images-x86_64
Summary:     U-Boot firmware images for x86_64 boards
BuildArch:   noarch

%description -n uboot-images-x86_64
U-Boot firmware binaries for x86_64 boards
%endif
%endif

%prep
%autosetup -p1 -n u-boot-v%{version}%{?candidate:-%{candidate}}

cp %SOURCE1 %SOURCE2 %SOURCE3 .

%build
mkdir builds

%make_build HOSTCC="gcc $RPM_OPT_FLAGS" CROSS_COMPILE="" tools-only_defconfig O=builds/
%make_build HOSTCC="gcc $RPM_OPT_FLAGS" CROSS_COMPILE="" tools-all O=builds/

%if %{with toolsonly}
# OpenSBI firmware is distributed in U-Boot SPL images
%ifarch riscv64
export OPENSBI=%{_datadir}/%{opensbi}/generic/firmware/fw_dynamic.bin
%endif

%ifarch aarch64 riscv64 x86_64
# Anatase only needs Raspberry Pi firmware on aarch64.
%ifarch aarch64
boards=rpi_arm64
%else
boards=$(cat %{_arch}-boards)
%endif
for board in $boards
do
  echo "Building board: $board"
  mkdir builds/$(echo $board)/


  make $(echo $board)_defconfig O=builds/$(echo $board)/
  %make_build HOSTCC="gcc $RPM_OPT_FLAGS" CROSS_COMPILE="" O=builds/$(echo $board)/

done

%endif
%endif

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_mandir}/man1
mkdir -p %{buildroot}%{_datadir}/uboot/

%if %{with toolsonly}
%ifarch aarch64
for board in $(ls builds)
do
 for file in u-boot.bin u-boot.img u-boot-dtb.img u-boot-sunxi-with-spl.bin u-boot-rockchip-spi.bin u-boot-rockchip.bin
 do
  if [ -f builds/$(echo $board)/$(echo $file) ]; then
    install -pD -m 0644 builds/$(echo $board)/$(echo $file) %{buildroot}%{_datadir}/uboot/$(echo $board)/$(echo $file)
  fi
 done
done

# Just for xilinx_zynqmp
for board in "xilinx_zynqmp_kria xilinx_zynqmp_virt"
do
 for file in u-boot.itb spl/boot.bin
 do
  if [ -f builds/$(echo $board)/$(echo $file) ]; then
    install -pD -m 0644 builds/$(echo $board)/$(echo $file) %{buildroot}%{_datadir}/uboot/$(echo $board)/$(echo $file)
  fi
 done
done

%endif

%ifarch riscv64
for board in $(ls builds)
do
 for file in u-boot.itb spl/u-boot-spl.bin spl/u-boot-spl.bin.normal.out
 do
  if [ -f builds/$(echo $board)/$(echo $file) ]; then
    install -pD -m 0644 builds/$(echo $board)/$(echo $file) %{buildroot}%{_datadir}/uboot/$(echo $board)/$(echo $file)
  fi
 done
done
%endif

%ifarch x86_64
for board in $(ls builds)
do
 for file in u-boot.rom
 do
  if [ -f builds/$(echo $board)/$(echo $file) ]; then
    install -pD -m 0644 builds/$(echo $board)/$(echo $file) %{buildroot}%{_datadir}/uboot/$(echo $board)/$(echo $file)
  fi
 done
done
%endif

# Bit of a hack to remove binaries we don't use as they're large
for board in $(ls builds)
do
  rm -f %{buildroot}%{_datadir}/uboot/$(echo $board)/u-boot.dtb
  if [ -f %{buildroot}%{_datadir}/uboot/$(echo $board)/u-boot-sunxi-with-spl.bin ]; then
    rm -f %{buildroot}%{_datadir}/uboot/$(echo $board)/u-boot{,-dtb}.*
  fi
  if [ -f %{buildroot}%{_datadir}/uboot/$(echo $board)/u-boot-rockchip.bin ]; then
    rm -f %{buildroot}%{_datadir}/uboot/$(echo $board)/u-boot{,-dtb}.*
  fi
done
%endif

for tool in dumpimage env/fw_printenv fdt_add_pubkey fit_check_sign fit_info gdb/gdbcont gdb/gdbsend gen_eth_addr gen_ethaddr_crc ifwitool img2srec kwboot mkeficapsule mkenvimage mkimage mksunxiboot ncb proftool sunxi-spl-image-builder
do
install -p -m 0755 builds/tools/$tool %{buildroot}%{_bindir}
done
for tool in dumpimage kwboot mkeficapsule mkimage
do
install -p -m 0644 doc/$tool.1 %{buildroot}%{_mandir}/man1
done

install -p -m 0755 builds/tools/env/fw_printenv %{buildroot}%{_bindir}
( cd %{buildroot}%{_bindir}; ln -sf fw_printenv fw_setenv )

%files
%license Licenses/*
%doc README doc/develop/distro.rst doc/README.gpt
%doc doc/develop/uefi doc/usage doc/arch/arm64.rst
%{_bindir}/*
%{_mandir}/man1/dumpimage.1*
%{_mandir}/man1/kwboot.1*
%{_mandir}/man1/mkeficapsule.1*
%{_mandir}/man1/mkimage.1*

%if %{with toolsonly}
%ifarch aarch64
%files -n uboot-images-armv8
%license Licenses/*
%dir %{_datadir}/uboot/
%{_datadir}/uboot/*
%endif

%ifarch riscv64
%files -n uboot-images-riscv64
%license Licenses/*
%dir %{_datadir}/uboot/
%{_datadir}/uboot/*
%endif

%ifarch x86_64
%files -n uboot-images-x86_64
%license Licenses/*
%dir %{_datadir}/uboot/
%{_datadir}/uboot/*
%endif
%endif

%changelog
* Tue Oct 06 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.10-1
- Update to 2026.10

* Tue Sep 08 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.10-0.4.rc4
- Update to 2026.10 RC4

* Thu Aug 27 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.10-0.3.rc3
- Update to 2026.10 RC3

* Wed Aug 12 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.10-0.2.rc2
- Update to 2026.10 RC2

* Thu Jul 30 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.10-0.1.rc1
- Update to 2026.10 RC1
- Update source URL

* Fri Jul 17 2026 Fedora Release Engineering <releng@fedoraproject.org> - 1:2026.07-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_45_Mass_Rebuild

* Tue Jul 07 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.07-1
- Update to 2026.07 GA

* Tue Jun 23 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.07-0.4.rc5
- Update to 2026.07 RC5

* Mon Jun 08 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.07-0.3.rc4
- Update to 2026.07 RC4

* Fri May 29 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.07-0.2.rc3
- Update to 2026.07 RC3
- Update U-Boot Project URL
- Update RPi PCIe patches
- Various RPi fixes

* Fri May 01 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.07-0.1.rc1
- Update to 2026.07 RC1

* Sat Apr 11 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.04-2
- Fix PCIe/USB on Raspberry Pi 4 (rhbz#2448365)
- Fix detection of some revisions of RPi5

* Tue Apr 07 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.04-1
- Update to 2026.04 GA

* Sun Mar 29 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.04-0.9.rc5
- Enable NVME booting on RPi5

* Tue Mar 24 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.04-0.8.rc5
- Update to 2026.04 RC5

* Sat Mar 14 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.04-0.7.rc4
- Raspberry Pi fixes

* Tue Mar 10 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.04-0.6.rc4
- Update to 2026.04 RC4

* Fri Feb 27 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.04-0.5.rc3
- Update to 2026.04 RC3

* Tue Feb 17 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.04-0.4.rc2
- Add initial bcm2712d0 identification

* Mon Feb 09 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.04-0.3.rc2
- Update to 2026.04 RC2

* Tue Jan 27 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.04-0.2.rc1
- Update to 2026.04 RC1

* Mon Jan 19 2026 Javier Martinez Canillas <javierm@redhat.com> - 1:2026.01-3
- Add a uboot-images-x86_64 subpackage

* Sat Jan 17 2026 Fedora Release Engineering <releng@fedoraproject.org> - 1:2026.01-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Tue Jan 06 2026 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.01-1
- Update to 2026.01 GA

* Mon Dec 29 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.01-0.4.rc5
- Update to 2026.01 RC5

* Mon Dec 08 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.01-0.3.rc4
- Update to 2026.01 RC4

* Fri Nov 28 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.01-0.2.rc3
- Updates for RPi

* Mon Nov 24 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2026.01-0.1.rc3
- Update to 2026.01 RC3

* Thu Oct 16 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.10-2
- Drop residual Rockchip firmware (saves ~150Mb)

* Mon Oct 13 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.10-1
- Update to 2025.10 GA (rhbz#2401964)
- Fix booting when using FW device-tree (rhbz#2402498)
- Fix for some variants of Raspberry Pi
- Fixes for Jetson device booting

* Fri Sep 26 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.10-0.7.rc5
- Update to 2025.10 RC5

* Mon Sep 08 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.10-0.6.rc4
- Update to 2025.10 RC4

* Sun Sep 07 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.10-0.5.rc3
- Boot fixes for some Raspberry Pi variants

* Wed Aug 27 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.10-0.4.rc3
- Fix booting on some Allwinner devices

* Mon Aug 25 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.10-0.3.rc3
- Update to 2025.10 RC3

* Tue Aug 19 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.10-0.2.rc2
- Fix and re-enable Jetson Nano

* Mon Aug 18 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.10-0.1.rc2
- Update to 2025.10 RC2

* Fri Jul 25 2025 Fedora Release Engineering <releng@fedoraproject.org> - 1:2025.07-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Thu Jul 10 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.07-2
- Update patch for rebase issue

* Wed Jul 09 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.07-1
- Update to 2025.07 GA

* Fri Jun 27 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.07-0.5.rc5
- Update to 2025.07 RC5
- Enable LWIP stack by default
- Enable HTTP(s) boot support

* Thu Jun 26 2025 Javier Martinez Canillas <javierm@redhat.com> - 1:2025.07-0.4.rc4
- Add EFI_PARTITION_INFO_PROTOCOL support

* Sun Jun 15 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.07-0.3.rc4
- Update to 2025.07 RC4

* Tue May 13 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.07-0.2.rc2
- Update to 2025.07 RC2

* Thu May 01 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.07-0.1.rc1
- Update to 2025.07 RC1

* Sun Apr 20 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.04-2
- Fix for RPi5 serial console

* Tue Apr 08 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.04-1
- Update to 2025.04 GA

* Tue Mar 25 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.04-0.7.rc5
- Update to 2025.04 RC5

* Wed Mar 12 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.04-0.6.rc4
- Update to 2025.04 RC4

* Wed Feb 26 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.04-0.5.rc3
- Update to 2025.04 RC3

* Tue Feb 18 2025 David Abdurachmanov <davidlt@rivosinc.com> - 1:2025.04-0.4.rc2
- Add support for riscv64

* Tue Feb 11 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.04-0.3.rc2
- Update to 2025.05 RC2

* Tue Feb 11 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.04-0.2.rc1
- Update to 2025.05 RC1

* Tue Jan 28 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.01-3
- Add new fdt_add_pubkey tool

* Sun Jan 19 2025 Fedora Release Engineering <releng@fedoraproject.org> - 1:2025.01-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Tue Jan 07 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.01-1
- Update to 2025.01 GA

* Mon Jan 06 2025 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.01-0.2.rc6
- Rebuild for TF-A 2.12

* Tue Dec 31 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2025.01-0.1.rc6
- Update to 2025.01 RC6

* Fri Oct 11 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.10-1
- Update to 2024.10 GA
- Fix passing RPi firmware CMA setting to kernel DT
- Update Geekbox

* Thu Oct 03 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.10-0.8.rc6
- Pass CMA FW setting through to kernel DT for Raspberry Pi

* Tue Oct 01 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.10-0.7.rc6
- Update to 2024.10 RC6

* Mon Sep 16 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.10-0.6.rc5
- Update to 2024.10 RC5

* Fri Sep  6 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.10-0.5.rc4
- Add missing licenses directory

* Tue Sep 03 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.10-0.4.rc4
- Update to 2024.10 RC4

* Mon Sep 02 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.10-0.3.rc3
- Fix Allwinner firmware chainloading (rhbz#2309138)
- Fix ATF firmware selection on a number of devices
- Support Allwinner SCP firmware (fixes suspend/resume)

* Tue Aug 27 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.10-0.2.rc3
- Update to 2024.10 RC3
- Enable initial QCM6490 SoC support

* Thu Aug 15 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.10-0.1.rc2
- Update to 2024.10 RC2

* Tue Jul 23 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.07-1
- Update to 2024.07

* Sat Jul 20 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1:2024.07-0.3.rc4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Tue Jun 18 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.07-0.2.rc4
- Update to 2024.07 RC4

* Sat May 25 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.07-0.1.rc3
- Update to 2024.07 RC3

* Wed Apr 03 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.04-1
- Update to 2024.04 GA
- Rockchip rk3328 USB fixes

* Wed Mar 27 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.04-0.8.rc5
- Update to 2024.04 RC5

* Thu Mar 21 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.04-0.7.rc4
- Updated patch for DTB loading

* Fri Mar 15 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.04-0.6.rc4
- Updated fix for FDT load

* Wed Mar 13 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.04-0.5.rc4
- Fixes for Rockchip rk3399 autoboot

* Tue Mar 12 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.04-0.4.rc4
- Update to 2024.04 RC4
- Initial fix for loading DT off /boot (rhbz 2247873)

* Thu Feb 29 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.04-0.3.rc3
- Update to 2024.04 RC3
- Enable a number of new upstream devices
- Upstream now builds Rockchip SPI artifacts
- Various cleanups
- Fix ESP partition detection to enable EFI vars

* Wed Feb 14 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.04-0.2.rc2
- Update to 2024.04 RC2

* Sat Jan 27 2024 Fedora Release Engineering <releng@fedoraproject.org> - 1:2024.01-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Mon Jan 08 2024 Peter Robinson <pbrobinson@fedoraproject.org> - 1:2024.01-1
- Update to 2024.01
