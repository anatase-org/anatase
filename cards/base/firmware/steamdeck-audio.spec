%global debug_package %{nil}
%global _binaries_in_noarch_packages_terminate_build 0
%global commit 7b98cc7a5276b2797e5a73120fac8fa1aba27ab1

Name:           steamdeck-audio
Version:        20260827
Release:        1%{?dist}
Summary:        Basic audio firmware and UCM configuration for Steam Deck OLED
License:        GPL-2.0-or-later
URL:            https://github.com/evlaV/valve-hardware-audio-processing
BuildArch:      noarch

Source0:        https://codeload.github.com/evlaV/valve-hardware-audio-processing/tar.gz/%{commit}#/valve-hardware-audio-processing-%{commit}.tar.gz

%description
Signed Sound Open Firmware binaries, topology, and ALSA UCM routes for the
Steam Deck OLED (Galileo) built-in audio device.

%prep
%autosetup -n valve-hardware-audio-processing-%{commit}

%build

%install
install -Dm0644 sof_fw/sof/sof-vangogh-code.bin \
    %{buildroot}%{_prefix}/lib/firmware/amd/sof/sof-vangogh-code.bin
install -Dm0644 sof_fw/sof/sof-vangogh-data.bin \
    %{buildroot}%{_prefix}/lib/firmware/amd/sof/sof-vangogh-data.bin
install -Dm0644 sof_fw/sof-tplg/sof-vangogh-nau8821-max.tplg \
    %{buildroot}%{_prefix}/lib/firmware/amd/sof-tplg/sof-vangogh-nau8821-max.tplg
install -Dm0644 ucm2/conf.d/sof-nau8821-max/HiFi.conf \
    %{buildroot}%{_datadir}/alsa/ucm2/conf.d/sof-nau8821-max/HiFi.conf
install -Dm0644 ucm2/conf.d/sof-nau8821-max/sof-nau8821-max.conf \
    %{buildroot}%{_datadir}/alsa/ucm2/conf.d/sof-nau8821-max/sof-nau8821-max.conf

%files
%license LICENSE
%dir %{_prefix}/lib/firmware/amd/sof
%dir %{_prefix}/lib/firmware/amd/sof-tplg
%{_prefix}/lib/firmware/amd/sof/sof-vangogh-code.bin
%{_prefix}/lib/firmware/amd/sof/sof-vangogh-data.bin
%{_prefix}/lib/firmware/amd/sof-tplg/sof-vangogh-nau8821-max.tplg
%dir %{_datadir}/alsa/ucm2/conf.d/sof-nau8821-max
%{_datadir}/alsa/ucm2/conf.d/sof-nau8821-max/HiFi.conf
%{_datadir}/alsa/ucm2/conf.d/sof-nau8821-max/sof-nau8821-max.conf
