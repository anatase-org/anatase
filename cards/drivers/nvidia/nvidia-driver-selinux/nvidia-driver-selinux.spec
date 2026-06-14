%global selinuxtype targeted
%global modulename nvidia-driver

Name:           nvidia-driver-selinux
Version:        0.1
Release:        2%{?dist}
Summary:        NVIDIA driver SELinux module
License:        GPL-3.0-only
URL:            https://negativo17.org
BuildArch:      noarch

Source0:        nvidia-driver.te
Source1:        LICENSE

BuildRequires:  selinux-policy-devel

Requires:       selinux-policy-%{selinuxtype}

Requires(post): libselinux-utils
Requires(post): policycoreutils
Requires(post): policycoreutils-python-utils
Requires(post): selinux-policy-base
Requires(post): selinux-policy-%{selinuxtype}

%description
NVIDIA driver SELinux policy module.

%prep
cp %{SOURCE0} %{SOURCE1} .

%build
make -f %{_datadir}/selinux/devel/Makefile %{modulename}.pp
bzip2 -9 %{modulename}.pp

%install
install -D -m 0644 %{modulename}.pp.bz2 %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}/%{modulename}.pp.bz2

%pre
%selinux_relabel_pre -s %{selinuxtype}

%post
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/%{modulename}.pp.bz2

%postun
if [ $1 -eq 0 ]; then
    %selinux_modules_uninstall -s %{selinuxtype} %{modulename}
fi

%posttrans
%selinux_relabel_post -s %{selinuxtype}

%files
%license LICENSE
%{_datadir}/selinux/packages/%{selinuxtype}/%{modulename}.pp.*
%ghost %verify(not md5 size mode mtime) %{_sharedstatedir}/selinux/%{selinuxtype}/active/modules/200/%{modulename}

%changelog
* Thu Mar 19 2026 Simone Caronni <negativo17@gmail.com> - 0.1-2
- Do not use the selinux_requires macro so we have more generic dependencies and
  we can install the generated packages also on RHEL z/EUS streams (#197).

* Tue Mar 17 2026 Simone Caronni <negativo17@gmail.com> - 0.1-1
- First build. Contains:
  * Future tmpfs support: https://github.com/fedora-selinux/selinux-policy/pull/3087
  * Current tmp_t write approach: https://github.com/negativo17/nvidia-driver/issues/196
