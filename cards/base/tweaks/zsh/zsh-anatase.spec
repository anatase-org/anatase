Name:           zsh-anatase
Summary:        Anatase zsh defaults and shell integrations
Version:        0.1.0
Release:        1%{?dist}
License:        MIT AND BSD-3-Clause AND GPL-2.0-only
%global debug_package %{nil}

# TODO: Pin these when we fork
Source0:        https://github.com/romkatv/powerlevel10k/archive/refs/heads/master.tar.gz#/powerlevel10k-master.tar.gz
Source1:        https://github.com/zsh-users/zsh-autosuggestions/archive/refs/heads/master.tar.gz#/zsh-autosuggestions-master.tar.gz
Source2:        https://github.com/zsh-users/zsh-syntax-highlighting/archive/refs/heads/master.tar.gz#/zsh-syntax-highlighting-master.tar.gz
Source3:        https://github.com/romkatv/libgit2/archive/refs/heads/master.tar.gz#/libgit2-master.tar.gz
Source4:        anatase.sh
Source5:        https://raw.githubusercontent.com/romkatv/powerlevel10k-media/master/MesloLGS%20NF%20Regular.ttf#/MesloLGS-NF-Regular.ttf
Source6:        https://raw.githubusercontent.com/romkatv/powerlevel10k-media/master/MesloLGS%20NF%20Bold.ttf#/MesloLGS-NF-Bold.ttf
Source7:        https://raw.githubusercontent.com/romkatv/powerlevel10k-media/master/MesloLGS%20NF%20Italic.ttf#/MesloLGS-NF-Italic.ttf
Source8:        https://raw.githubusercontent.com/romkatv/powerlevel10k-media/master/MesloLGS%20NF%20Bold%20Italic.ttf#/MesloLGS-NF-Bold-Italic.ttf
Source9:        anatase-logo-mono.svg
Source10:       patch-meslo-anatase.py

BuildRequires:  cmake
BuildRequires:  fontforge
BuildRequires:  gcc-c++
BuildRequires:  git-core
BuildRequires:  make
BuildRequires:  tar
Requires:       zsh

%description
Anatase zsh plugins and shell integrations.

%prep
%setup -q -c -T
tar -xzf %{SOURCE0}
tar -xzf %{SOURCE1}
tar -xzf %{SOURCE2}
cp -p powerlevel10k-master/LICENSE LICENSE.powerlevel10k
cp -p powerlevel10k-master/gitstatus/LICENSE LICENSE.gitstatus
cp -p zsh-autosuggestions-master/LICENSE LICENSE.zsh-autosuggestions
cp -p zsh-syntax-highlighting-master/COPYING.md LICENSE.zsh-syntax-highlighting
tar -xOf %{SOURCE3} libgit2-master/COPYING > LICENSE.libgit2
libgit2_sha256="$(sha256sum -b %{SOURCE3} | cut -d' ' -f1)"
sed -i \
    -e 's/^libgit2_version=.*/libgit2_version="master"/' \
    -e "s/^libgit2_sha256=.*/libgit2_sha256=\"$libgit2_sha256\"/" \
    powerlevel10k-master/gitstatus/build.info
install -Dm0644 %{SOURCE3} powerlevel10k-master/gitstatus/deps/libgit2-master.tar.gz
sed -i 's/gitstatus_ldflags="$gitstatus_ldflags ${static_pie:--static}"/gitstatus_ldflags="$gitstatus_ldflags"/g' powerlevel10k-master/gitstatus/build

%build
cd powerlevel10k-master/gitstatus
mkdir -p .tmp
TMPDIR="$PWD/.tmp" ./build -m %{_target_cpu}

%install
install -dm0755 %{buildroot}%{_datadir}/anatase/zsh
install -dm0755 %{buildroot}%{_datadir}/fonts/anatase
cp -a powerlevel10k-master %{buildroot}%{_datadir}/anatase/zsh/powerlevel10k
cp -a zsh-autosuggestions-master %{buildroot}%{_datadir}/anatase/zsh/zsh-autosuggestions
cp -a zsh-syntax-highlighting-master %{buildroot}%{_datadir}/anatase/zsh/zsh-syntax-highlighting
install -Dm0644 %{SOURCE4} %{buildroot}%{_datadir}/anatase/zsh/anatase.sh
fontforge -script %{SOURCE10} %{SOURCE5} %{SOURCE9} %{buildroot}%{_datadir}/fonts/anatase/MesloLGS-NF-Regular.ttf
fontforge -script %{SOURCE10} %{SOURCE6} %{SOURCE9} %{buildroot}%{_datadir}/fonts/anatase/MesloLGS-NF-Bold.ttf
fontforge -script %{SOURCE10} %{SOURCE7} %{SOURCE9} %{buildroot}%{_datadir}/fonts/anatase/MesloLGS-NF-Italic.ttf
fontforge -script %{SOURCE10} %{SOURCE8} %{SOURCE9} %{buildroot}%{_datadir}/fonts/anatase/MesloLGS-NF-Bold-Italic.ttf
rm -rf %{buildroot}%{_datadir}/anatase/zsh/powerlevel10k/gitstatus/.tmp
rm -f %{buildroot}%{_datadir}/anatase/zsh/powerlevel10k/gitstatus/deps/*.tar.gz

find %{buildroot}%{_datadir}/anatase/zsh -type d -exec chmod 0755 {} +
find %{buildroot}%{_datadir}/anatase/zsh -type f -exec chmod 0644 {} +
find %{buildroot}%{_datadir}/fonts/anatase -type f -exec chmod 0644 {} +
chmod 0755 %{buildroot}%{_datadir}/anatase/zsh/powerlevel10k/gitstatus/usrbin/gitstatusd

%files
%license LICENSE.powerlevel10k
%license LICENSE.gitstatus
%license LICENSE.libgit2
%license LICENSE.zsh-autosuggestions
%license LICENSE.zsh-syntax-highlighting
%{_datadir}/anatase/zsh/
%{_datadir}/fonts/anatase/

%changelog
