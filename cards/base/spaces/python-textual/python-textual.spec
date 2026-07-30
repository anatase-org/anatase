Name:           python-textual
Version:        8.1.1
Release:        3%{?dist}
Summary:        TUI (Text User Interface) framework for Python
License:        MIT
URL:            https://github.com/Textualize/textual
Source0:        %{url}/archive/v%{version}/textual-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python3-devel
# Test dependencies:
BuildRequires:  pytest
BuildRequires:  python3-jinja2
BuildRequires:  python3-syrupy
BuildRequires:  python3-time-machine
BuildRequires:  python3-pytest-asyncio
BuildRequires:  python3-aiohttp
BuildRequires:  python3-pytest-aiohttp

%global _description %{expand:
Textual is a TUI (Text User Interface) framework for Python inspired
by modern web development. Currently a Work in Progress.}

%description
%{_description}

%package -n python3-textual
Summary:        %{summary}

%description -n python3-textual
%{_description}

%package -n python3-textual-doc
Summary:        Docs and examples for python3-textual

%description -n python3-textual-doc
%{_description}

%prep
%autosetup -n textual-%{version}
# Fedora 44 provides the linkify dependency separately and Pygments 2.19.1.
sed -i 's/markdown-it-py = { extras = \["linkify"\], version = ">=2.1.0" }/markdown-it-py = ">=2.1.0"/' pyproject.toml
sed -i 's/pygments = "\^2\.19\.2"/pygments = "^2.19.1"/' pyproject.toml

%generate_buildrequires
%pyproject_buildrequires -r


%build
%pyproject_wheel


%install
%pyproject_install
%pyproject_save_files textual


%files -n python3-textual -f %{pyproject_files}
%license LICENSE

%files -n python3-textual-doc
%license LICENSE
%doc README.md docs/ examples/


%changelog
* Thu Jul 16 2026 Fedora Release Engineering <releng@fedoraproject.org> - 8.1.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_45_Mass_Rebuild

* Thu Jun 04 2026 Python Maint <python-maint@redhat.com> - 8.1.1-2
- Rebuilt for Python 3.15

* Thu May 14 2026 Maxime Ripard <mripard@kernel.org> - 8.1.1-1
- Update to 8.1.1

* Sat Jan 17 2026 Fedora Release Engineering <releng@fedoraproject.org> - 4.0.0-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_44_Mass_Rebuild

* Fri Sep 19 2025 Python Maint <python-maint@redhat.com> - 4.0.0-4
- Rebuilt for Python 3.14.0rc3 bytecode

* Fri Aug 15 2025 Python Maint <python-maint@redhat.com> - 4.0.0-3
- Rebuilt for Python 3.14.0rc2 bytecode

* Fri Jul 25 2025 Fedora Release Engineering <releng@fedoraproject.org> - 4.0.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_43_Mass_Rebuild

* Fri Jul 18 2025 Jonathan Wright <jonathan@almalinux.org> - 4.0.0-1
- update to 4.0.0 rhbz#2345983

* Wed Jun 04 2025 Python Maint <python-maint@redhat.com> - 1.0.0-2
- Rebuilt for Python 3.14

* Thu Jan 23 2025 Jonathan Wright <jonathan@almalinux.org> - 1.0.0-1
- update to 1.0.0 rhbz#2282650

* Sat Jan 18 2025 Fedora Release Engineering <releng@fedoraproject.org> - 0.69.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_42_Mass_Rebuild

* Fri Jul 19 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.69.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_41_Mass_Rebuild

* Mon Jun 17 2024 Jonathan Wright <jonathan@almalinux.org> - 0.69.0-1
- update to 0.69.0 rhbz#2282650

* Sun Jun 09 2024 Python Maint <python-maint@redhat.com> - 0.62.0-2
- Rebuilt for Python 3.13

* Tue May 21 2024 Jonathan Wright <jonathan@almalinux.org> - 0.62.0-1
- update to 0.62.0 rhbz#2273769

* Fri Apr 05 2024 Jonathan Wright <jonathan@almalinux.org> - 0.55.1-1
- Update to 0.55.1 rhbz#2262427

* Thu Feb 01 2024 Jonathan Wright <jonathan@almalinux.org> - 0.48.1-1
- Update to 0.48.1 rhbz#2256835

* Fri Jan 26 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.46.0-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Mon Jan 22 2024 Fedora Release Engineering <releng@fedoraproject.org> - 0.46.0-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_40_Mass_Rebuild

* Wed Jan 03 2024 Jonathan Wright <jonathan@almalinux.org> - 0.46.0-1
- Update to 0.46.0 rhbz#2254910

* Tue Dec 12 2023 Jonathan Wright <jonathan@almalinux.org> - 0.45.1-1
- Update to 0.45.1 rhbz#2254187

* Wed Dec 06 2023 Jonathan Wright <jonathan@almalinux.org> - 0.44.1-1
- Update to 0.44.1 rhbz#2252397

* Thu Nov 30 2023 Jonathan Wright <jonathan@almalinux.org> - 0.43.2-1
- Update to 0.43.2 rhbz#2239239

* Fri Sep 15 2023 Jonathan Wright <jonathan@almalinux.org> - 0.37.0-1
- Update to 0.37.0 rhbz#2192888

* Fri Jul 21 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0.22.3-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_39_Mass_Rebuild

* Fri Apr 28 2023 Jonathan Wright <jonathan@almalinux.org> - 0.22.3-1
- Update to 0.22.3 rhbz#2170877

* Sat Mar 25 2023 Jonathan Wright <jonathan@almalinux.org> - 0.16.0-1
- Update to 0.16.0 rhbz#2170877

* Wed Feb 15 2023 Jonathan Wright <jonathan@almalinux.org> - 0.10.0-1
- Update to 0.10.0 rhbz#2162484

* Fri Jan 20 2023 Fedora Release Engineering <releng@fedoraproject.org> - 0.1.18-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_38_Mass_Rebuild

* Sun Jul 31 2022 Jonathan Wright <jonathan@almalinux.org> - 0.1.18-1
- Initial package build
- rhbz#2121258
