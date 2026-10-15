Name:           hhd-power-profiles
Version:        1
Release:        2%{?dist}
Summary:        Power profile package compatibility for HHD
License:        MIT
BuildArch:      noarch
Source0:        power-profiles-daemon.conf.in
Source1:        power-profiles-daemon.dbus.xml.in
Requires:       hhd
Provides:       tuned
Provides:       tuned-ppd
Provides:       power-profiles-daemon
Conflicts:      tuned
Conflicts:      tuned-ppd
Conflicts:      power-profiles-daemon

%description
Satisfy power profile package dependencies using HHD's power-profiles API.
Prevent tuned, tuned-ppd, and power-profiles-daemon from being installed
alongside HHD. This package supplies the D-Bus configuration and interfaces
for HHD's power-profiles API.

%install
install -dm0755 %{buildroot}%{_datadir}/dbus-1/{system.d,interfaces}
for dbus_name in org.freedesktop.UPower.PowerProfiles net.hadess.PowerProfiles; do
    dbus_path="/$(printf '%s' "$dbus_name" | tr . /)"
    sed -e "s|@dbus_name@|$dbus_name|g" \
        -e "s|@dbus_iface@|$dbus_name|g" \
        %{SOURCE0} > "%{buildroot}%{_datadir}/dbus-1/system.d/$dbus_name.conf"
    sed -e "s|@dbus_iface@|$dbus_name|g" \
        -e "s|@dbus_path@|$dbus_path|g" \
        %{SOURCE1} > "%{buildroot}%{_datadir}/dbus-1/interfaces/$dbus_name.xml"
done

%files
%{_datadir}/dbus-1/system.d/org.freedesktop.UPower.PowerProfiles.conf
%{_datadir}/dbus-1/system.d/net.hadess.PowerProfiles.conf
%{_datadir}/dbus-1/interfaces/org.freedesktop.UPower.PowerProfiles.xml
%{_datadir}/dbus-1/interfaces/net.hadess.PowerProfiles.xml
