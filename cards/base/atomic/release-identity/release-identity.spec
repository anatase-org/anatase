# Anaconda selects Slitherer by RPM release identity, independently of the
# webui_web_engine setting. Provide that identity without Fedora branding files.
Name:           fedora-release-identity-kde-desktop
Version:        1
Release:        1%{?dist}
Summary:        Release identity compatibility for Anatase's installer
License:        MIT
BuildArch:      noarch
Provides:       fedora-release-identity
Provides:       fedora-release-identity-kde

%description
An empty release identity package that selects Slitherer for Anaconda's
conditional browser dependency. Anatase supplies its own release information
and branding, so this package installs no files or Fedora presets.

%files
